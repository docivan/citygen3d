import numpy as np

import settings
import model3d

__UP = 1
__DOWN = 2
__LEFT = 3
__RIGHT = 4


def __gen_roof_decor(roof_rect):
    #TODO
    return


# ((s_ratio, h_ratio)) - all relative; notes:
# s_ratio is rel to the longest side; it is the scaled to be uniform for short side
# s_ratio denotes INDENT from the outsiden inwards of each block!
# h_ratio is rel to height
def __gen_bld_elem_style():
    style = []

    expander_idx = -1

    for idx,prob in enumerate(settings.settings["bld_boxy_segm_prob"]):
        if np.random.uniform() < prob:
            if np.random.uniform(0, settings.settings["bld_boxy_segm_h_max"][idx]) < 0:
                expander_idx = idx
                continue

            style.append((np.random.uniform(0, settings.settings["bld_boxy_segm_step_max"][idx]),
                          np.random.uniform(0, settings.settings["bld_boxy_segm_h_max"][idx])))

    if expander_idx != -1:
        h_rest = 1.
        for (s_ratio, h_ratio) in style:
            h_rest -= h_ratio

        print("hrest", h_rest)
        style.insert(expander_idx, (np.random.uniform(0, settings.settings["bld_boxy_segm_step_max"][idx]), h_rest))

    print(style)
    return style


def __render_segm(rect, z1, z2, style, sides=(__UP, __DOWN, __LEFT, __RIGHT)):
    assert len(sides) > 0
    assert len(sides) <= 4
    assert z2>z1

    short_side = min(abs(rect[0] - rect[2]), abs(rect[1] - rect[3]))
    cumul_z = z1

    for s in style:
        w_abs = short_side * s[0]
        segm_rect = list(rect)
        #segm_rect = (rect[0] + w_abs, rect[1] + w_abs, rect[2] - w_abs, rect[3] - w_abs)

        if __UP in sides:
            segm_rect[3] -= w_abs
        if __DOWN in sides:
            segm_rect[1] += w_abs
        if __LEFT in sides:
            segm_rect[0] += w_abs
        if __RIGHT in sides:
            segm_rect[2] -= w_abs

        print("z-s:", z1, z2)
        model3d.cube_2dh(segm_rect, height=(z2-z1)*s[1], z=cumul_z)
        cumul_z += (z2-z1)*s[1]


def __gen_bld_pyramid(rect, h):
    box_cnt = np.random.randint(settings.settings["bld_pyramid_box_cnt_min"], settings.settings["bld_pyramid_box_cnt_max"])

    # TODO this should be done the same way as the above segment gen/rndr
    zcoords = []
    widths = []

    short_side = min(abs(rect[0]-rect[2]), abs(rect[1]-rect[3]))

    for i in range(box_cnt - 1):
        zcoords.append(np.random.uniform(settings.settings["bld_sq_min"], h))
        # fraction of base size
        widths.append( np.random.uniform((np.random.uniform(settings.settings["bld_sq_min"])/short_side),
                                         1.-box_cnt*0.05 + i*0.05) )

    zcoords.sort()
    widths.sort(reverse=True)

    print("zcoords", zcoords, box_cnt, h)

    # generate boxes
    for idx,z in enumerate(zcoords):
        w_abs = (short_side - short_side * widths[idx])/2

        assert w_abs * 2 < abs(rect[0] - rect[2])
        assert w_abs * 2 < abs(rect[1] - rect[3])

        segm_rect = (rect[0] + w_abs, rect[1] + w_abs, rect[2] - w_abs, rect[3] - w_abs)

        zprev = zcoords[idx-1]
        if idx == 0:
            zprev = 0

        print("pyramid:", z*h, z, zprev)
        __render_segm(segm_rect, zprev, z, __gen_bld_elem_style())

    # TODO facade decor (lines / stripes +++)
    # TODO generate roof decor
    # -- antennae
    # -- helipad
    # -- garden!

def __distrib(falloff = 100, cutoff = 0.1):
    # TODO cutoff!
    return 1 - (pow(falloff, np.random.uniform()) - 1) / (falloff - 1)



def __gen_bld_boxy(rect, h):
    x_div = np.random.randint(settings.settings["bld_boxy_div_min"], settings.settings["bld_boxy_div_max"])
    y_div = np.random.randint(settings.settings["bld_boxy_div_min"], settings.settings["bld_boxy_div_max"])

    x_unit = (rect[2]-rect[0]) / x_div
    y_unit = (rect[3]-rect[1]) / y_div

    towers = []
    tower_cnt = np.random.randint(settings.settings["bld_boxy_towers_min"], settings.settings["bld_boxy_towers_max"])

    for i in range(tower_cnt):
        tx1 = np.random.randint(0, x_div)
        tx2 = np.random.randint(0, x_div)
        ty1 = np.random.randint(0, y_div)
        ty2 = np.random.randint(0, y_div)

        x1 = min(tx1, tx2)
        x2 = max(tx1, tx2)
        y1 = min(ty1, ty2)
        y2 = max(ty1, ty2)

        h = settings.settings["bld_sq_min"] + (h-settings.settings["bld_sq_min"])*__distrib()
        print(h)
        style = __gen_bld_elem_style()

        towers.append(([x1, y1, x2, y2], h, style))

    grid = np.full((y_div, x_div), -1)

    for x in range(x_div):
        for y in range(y_div):
            for idx, tower in enumerate(towers):
                if x >= tower[0][0] and x<= tower[0][2] and y >= tower[0][1] and y<= tower[0][3]:
                    if grid[y][x] != -1 or tower[2] > towers[grid[y][x]][2]:
                        grid[y][x] = idx

    for x in range(x_div):
        for y in range(y_div):
            if grid[y][x] != -1:
                model3d.cube_2dh((rect[0] + x * x_unit,
                                  rect[1] + y * y_unit,
                                  rect[0] + (x+1) * x_unit,
                                  rect[1] + (y+1) * y_unit),
                                 towers[grid[y][x]][1])

    print(x_div, y_div, x_unit, y_unit, tower_cnt)
    print(grid)


def generate(bld_areas):
    print("Generating buildings...")
    for idx, a in enumerate(bld_areas):
        p = np.random.uniform()
        # TODO height map
        print("- building", idx+1, "of", len(bld_areas))

        if p < settings.settings["bld_pyramid_prob"]:
            __gen_bld_pyramid(a, np.random.uniform(settings.settings["bld_h_min"], settings.settings["bld_h_max"]))
        else:
            __gen_bld_boxy(a, np.random.uniform(settings.settings["bld_h_min"], settings.settings["bld_h_max"]))
