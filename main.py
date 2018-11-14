import numpy as np
import random
import math
import cv2
import sys

import model3d
import streets
import settings


if len(sys.argv) != 2:
    print("Usage: citygen3d.py settings_file")
    quit(0)

settings.load(sys.argv[1])

###########################################################################################
# config, sizes in m
# should at some point be transferred to a json encoded config file
width = 1200.
height = 1200.
seed = 12345

board_thickness = 5  # NB! units?!?
skirt_size = 10  # m

main_st_prob = 0.2
main_st_w_min = 80
main_st_w_max = 100

small_st_w_min = 20
small_st_w_max = 40

block_w_min = 100
block_w_max = 300

# building settings

bld_h_min = 6
bld_h_max = 300

bld_s_min = 30
bld_s_max = 300

# TODO!


# park settings

park_replaces_bld_prob = 0.05  # probability that a park square will replace a building
tree_pine_ratio = 0.5
tree_fill_min = 0.2  # % of space filled with trees
tree_fill_max = 0.8
tree_sz_max = 20
tree_sz_min = 10

###########################################################################################
# internal config

print("Initialising...")

__debug = True

__disp_img_w = 800.
__disp_img_h = 800.

__board_w = width + skirt_size * 2
__board_h = height + skirt_size * 2

random.seed(seed)
np.random.seed(seed)

if width < block_w_max * 2:
    print("WARNING! Board width should be at least twice the block width. Changed to minimum value.")
    print("Got:", width, ", but need at least", block_w_max * 2)
    width = block_w_max * 2

if height < block_w_max * 2:
    print("WARNING! Board height should be at least twice the block width. Changed to minimum value.")
    print("Got:", height, ", but need at least", block_w_max * 2)
    height = block_w_max * 2

model3d.init("test.stl")
model3d.cube_2v((0, 0, -board_thickness), (width + skirt_size * 2, height + skirt_size * 2, 0))

###########################################################################################
# block generation
print("Generating city blocks...")


def gen_block_and_street():
    # gen random block size + streed size
    block = random.randint(block_w_min, block_w_max)

    street = 0
    if random.random() < main_st_prob:
        street = random.randint(main_st_w_min, main_st_w_max)
    else:
        street = random.randint(small_st_w_min, small_st_w_max)

    return block, street


def gen_blocks(dim):
    blocks = []
    sts = []

    cur_x = 0
    last_one = False

    while True:
        block, street = gen_block_and_street()

        block_from = cur_x
        block_to = cur_x + block

        cur_x = block_to + street

        sts.append((skirt_size + block_to, street))

        blocks.append((skirt_size + block_from, skirt_size + block_to))

        # allocate the remaining space to the last block
        if last_one:
            blocks.append((skirt_size + cur_x, skirt_size + dim))
            # print((skirt_size + cur_x, skirt_size + dim))
            break

        if not last_one and (dim - cur_x) < (block_w_max + block_w_min + main_st_w_max):
            if (dim - cur_x) < block_w_max and (dim - cur_x) > block_w_min:
                blocks.append((skirt_size + cur_x, skirt_size + dim))
                break
            else:
                last_one = True
    return blocks, sts


# generate grid:
# - number of horiz streets

blocks_x, streets.streets_x = gen_blocks(width)
blocks_y, streets.streets_y = gen_blocks(height)

# recode into something sensible
block_areas = []
for h in blocks_x:
    for v in blocks_y:
        x1 = int(h[0])
        y1 = int(v[0])

        x2 = int(h[1])
        y2 = int(v[1])

        block_areas.append((x1, y1, x2, y2))

print("- horisontal blocks:", len(blocks_x))
print("- vertical blocks:", len(blocks_y))
print("- total blocks:", len(block_areas))

###########################################################################################
# generate streets

streets.generate()


###########################################################################################
# split blocks

print("Dividing blocks into building spaces...")


# returns empty list if unable to split
def split_rect_once(rect, min_w, max_w):
    assert len(rect) == 4
    assert rect[0] < rect[2], "{}".format(rect)
    assert rect[1] < rect[3], "{}".format(rect)

    w = rect[2] - rect[0]
    h = rect[3] - rect[1]

    # generate a list of possible rects
    possible_rects = []

    if h >= (min_w * 2):
        for split_line in range(min_w, h - min_w + 1):
            rect1 = (rect[0], rect[1], rect[2], rect[1] + split_line)
            rect2 = (rect[0], rect[1] + split_line, rect[2], rect[3])
            possible_rects.append([rect1, rect2])

    if w >= (min_w * 2):
        for split_line in range(min_w, w - min_w + 1):
            rect1 = (rect[0], rect[1], rect[0] + split_line, rect[3])
            rect2 = (rect[0] + split_line, rect[1], rect[2], rect[3])
            possible_rects.append([rect1, rect2])

    if len(possible_rects) == 0:
        return []
    else:
        # pick a random one and return
        idx = random.randint(0, len(possible_rects) - 1)
        return possible_rects[idx]


def split_rect(rect, min_w, max_w):
    assert (len(rect) == 4)

    active = []
    passive = []

    active.append(rect)

    while len(active) > 0:
        # choose random rect
        idx = random.randint(0, len(active) - 1)
        # print(idx, "/", len(active), active[idx])
        new_rects = split_rect_once(active[idx], min_w, max_w)

        if len(new_rects) != 2:  # unable to split
            passive.append(active[idx])
            active.pop(idx)
        else:
            # print(active[idx], "=>", new_rects)
            active.pop(idx)
            active = active + new_rects

    return passive


building_areas = []
building_areas_cnt = 0

for b in block_areas:
    buildings = split_rect(b, bld_s_min, bld_s_max)
    building_areas.append(buildings)
    building_areas_cnt += len(buildings)

print("-total building spaces:", building_areas_cnt)

###########################################################################################
# now generating contents
print("Populating building spaces...")

if __debug:
    img = np.zeros((int(__board_h), int(__board_w), 3), np.uint8)


def gen_tree(rect):
    diameter = 0
    x = 0
    y = 0

    # choose shortest side
    if rect[2] - rect[0] < rect[3] - rect[1]:
        diameter = rect[2] - rect[0]
        # since x is shortest
        x = rect[0] + diameter / 2.  # TODO in case of float, this will collide trees
        y = random.uniform(rect[1] + diameter / 2., rect[3] - diameter / 2.)
    else:
        diameter = rect[3] - rect[1]
        # since y is shortest
        y = rect[1] + diameter / 2.  # TODO in case of float, this will collide trees
        x = random.uniform(rect[0] + diameter / 2., rect[2] - diameter / 2.)

    # ofile.write("cube([{}, {}, {}]);}}\n".format(rect[2]-rect[0],rect[3]-rect[1],10))

    if random.random() < tree_pine_ratio:
        a = 1
        # TODO - implement!
        # ofile.write("translate([{}, {}, {}]){{".format(x, y, -diameter/2))
        # ofile.write("cylinder(h={}, r1=0, r2={}, center=true);}}\n".format(diameter*1.5, diameter/2))
    else:
        model3d.sphere((x, y, diameter / 2.), diameter)

    # TODO: stem

    if __debug:
        # cv2.rectangle(img,(rect[0],rect[1]),(rect[2],rect[3]),
        #		(random.randint(0,254),random.randint(0,254),random.randint(0,254)),-1)
        cv2.circle(img, (int(x), int(y)), int(diameter / 2), (0, 0, 0), thickness=1)


def gen_park(rect):
    potential_trees = split_rect(rect, tree_sz_min, tree_sz_max)

    fill = random.uniform(tree_fill_min, tree_fill_max)
    tree_cnt = int(math.floor(len(potential_trees) * fill))

    # print("Park:", tree_cnt, "of", len(potential_trees), "used")

    for i in range(tree_cnt):
        idx = random.randint(0, len(potential_trees) - 1)
        gen_tree(potential_trees[idx])
        potential_trees.pop(idx)


def gen_building(rect):
    # TODO this is just a placeholder
    model3d.cube_2dh(rect, height=random.randint(bld_h_min, bld_h_max))


for idx,block in enumerate(block_areas):
    print("- block", idx+1, "of", len(block_areas))

    for bld_area in building_areas[idx]:
        if __debug:
            cv2.rectangle(img, (bld_area[0], bld_area[1]), (bld_area[2], bld_area[3]),
                          (random.randint(0, 254), random.randint(0, 254), random.randint(0, 254)), -1)

        edge = False

        for i in range(4):
            if model3d.cmp_float(block[i], bld_area[i]):
                edge = True
                break

        if edge:
            gen_building(bld_area)
        else:
            gen_park(bld_area)


print("Cleaning up...")
model3d.deinit()

if __debug:
    cv2.imwrite("out_s" + str(seed) + ".png", img)
