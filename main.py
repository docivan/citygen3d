import numpy as np
import random
import math
import cv2
import sys

import model3d
import streets
import settings
import buildings


if len(sys.argv) != 2:
    print("Usage: citygen3d.py settings_file")
    quit(0)

settings.load(sys.argv[1])

###########################################################################################
# internal config

print("Initialising...")

__debug = True

__disp_img_w = 800.
__disp_img_h = 800.

__board_w = settings.settings["width"] + settings.settings["skirt_size"] * 2
__board_h = settings.settings["height"] + settings.settings["skirt_size"] * 2

random.seed(settings.settings["seed"])
np.random.seed(settings.settings["seed"])

if settings.settings["width"] < settings.settings["block_w_max"] * 2:
    print("WARNING! Board width should be at least twice the block width. Changed to minimum value.")
    print("Got:", settings.settings["width"], ", but need at least", settings.settings["block_w_max"] * 2)
    settings.settings["width"] = settings.settings["block_w_max"] * 2

if settings.settings["height"] < settings.settings["block_w_max"] * 2:
    print("WARNING! Board height should be at least twice the block width. Changed to minimum value.")
    print("Got:", settings.settings["height"], ", but need at least", settings.settings["block_w_max"] * 2)
    settings.settings["height"] = settings.settings["block_w_max"] * 2

model3d.init("output.stl")
model3d.cube_2v((0, 0, -settings.settings["board_thickness"]),
                (settings.settings["width"] + settings.settings["skirt_size"] * 2, settings.settings["height"] +
                 settings.settings["skirt_size"] * 2, 0))


###########################################################################################
# block generation
print("Generating city blocks...")


def gen_block_and_street():
    # gen random block size + streed size
    block = random.randint(settings.settings["block_w_min"], settings.settings["block_w_max"])

    street = 0
    if random.random() < settings.settings["main_st_prob"]:
        street = random.randint(settings.settings["main_st_w_min"], settings.settings["main_st_w_max"])
    else:
        street = random.randint(settings.settings["small_st_w_min"], settings.settings["small_st_w_max"])

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

        sts.append((settings.settings["skirt_size"] + block_to, street))

        blocks.append((settings.settings["skirt_size"] + block_from, settings.settings["skirt_size"] + block_to))

        # allocate the remaining space to the last block
        if last_one:
            blocks.append((settings.settings["skirt_size"] + cur_x, settings.settings["skirt_size"] + dim))
            # print((skirt_size + cur_x, skirt_size + dim))
            break

        if not last_one and (dim - cur_x) < (settings.settings["block_w_max"] + settings.settings["block_w_min"] +
                                             settings.settings["main_st_w_max"]):
            if (dim - cur_x) < settings.settings["block_w_max"] and (dim - cur_x) > settings.settings["block_w_min"]:
                blocks.append((settings.settings["skirt_size"] + cur_x, settings.settings["skirt_size"] + dim))
                break
            else:
                last_one = True
    return blocks, sts


# generate grid:
# - number of horiz streets

blocks_x, streets.streets_x = gen_blocks(settings.settings["width"])
blocks_y, streets.streets_y = gen_blocks(settings.settings["height"])

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
    blds = split_rect(b, settings.settings["bld_s_min"], settings.settings["bld_s_max"])
    building_areas.append(blds)
    building_areas_cnt += len(blds)

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

    if random.random() < settings.settings["tree_pine_ratio"]:
        model3d.cone((x, y, 0), diameter,
                     np.random.uniform(settings.settings["tree_sz_min"], settings.settings["tree_sz_max"]))
    else:
        model3d.sphere_cubed((x, y, diameter / 2. * 1.5), diameter, ratio = 1./3./2.)
        #trunk
        s = diameter/2. - diameter/3./2.
        model3d.cube_2v((x-s,y-s,0), (x+s,y+s,diameter/4.))

    if __debug:
        # cv2.rectangle(img,(rect[0],rect[1]),(rect[2],rect[3]),
        #		(random.randint(0,254),random.randint(0,254),random.randint(0,254)),-1)
        cv2.circle(img, (int(x), int(y)), int(diameter / 2), (0, 0, 0), thickness=1)


def gen_park(rect):
    potential_trees = split_rect(rect, settings.settings["tree_sz_min"], settings.settings["tree_sz_max"])

    fill = random.uniform(settings.settings["tree_fill_min"], settings.settings["tree_fill_max"])
    tree_cnt = int(math.floor(len(potential_trees) * fill))

    # print("Park:", tree_cnt, "of", len(potential_trees), "used")

    for i in range(tree_cnt):
        idx = random.randint(0, len(potential_trees) - 1)
        gen_tree(potential_trees[idx])
        potential_trees.pop(idx)


def gen_building(rect):
    # TODO this is just a placeholder
    model3d.cube_2dh(rect, height=random.randint(settings.settings["bld_h_min"], settings.settings["bld_h_max"]))

bld_areas = []

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
            bld_areas.append(bld_area)
        else:
            gen_park(bld_area)


buildings.generate(bld_areas)


print("Cleaning up...")
model3d.deinit()

if __debug:
    cv2.imwrite("bld_areas.png", img)
