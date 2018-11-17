import numpy as np
import random
import sys

import model3d
import streets
import settings
import buildings
import parks
import utils


if len(sys.argv) != 2:
    print("Usage: citygen3d.py settings_file")
    quit(0)

settings.load(sys.argv[1])

###########################################################################################
# internal config

print("Initialising...")

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

building_areas = []
building_areas_cnt = 0

for b in block_areas:
    blds = utils.split_rect(b, settings.settings["bld_s_min"], settings.settings["bld_s_max"])
    building_areas.append(blds)
    building_areas_cnt += len(blds)

print("-total building spaces:", building_areas_cnt)

###########################################################################################
# now generating contents
print("Populating building spaces...")

bld_areas = []

for idx,block in enumerate(block_areas):
    print("- block", idx+1, "of", len(block_areas))

    for bld_area in building_areas[idx]:
        edge = False

        for i in range(4):
            if utils.cmp_float(block[i], bld_area[i]):
                edge = True
                break

        if edge:
            bld_areas.append(bld_area)
        else:
            parks.gen_park(bld_area)


buildings.generate(bld_areas)

print("Cleaning up...")
model3d.deinit()
