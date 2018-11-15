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

        style.insert(expander_idx, (np.random.uniform(0, settings.settings["bld_boxy_segm_step_max"][idx]), h_rest))

    return style


def __render_segm(rect, z1, z2, style, sides=(__UP, __DOWN, __LEFT, __RIGHT)):
    assert len(sides) > 0
    assert len(sides) <= 4
    assert z2>z1

    #long_side = max(abs(rect[0] - rect[2]), abs(rect[1] - rect[3]))
    short_side = min(abs(rect[0] - rect[2]), abs(rect[1] - rect[3]))

    for s in style:
        segm_rect = []
        cumul_z = z1

        for i in range(4):
            segm_rect.append(rect[i] + short_side * s[0])

        model3d.cube_2dh(segm_rect, height=(z2-z1)*s[1], z=cumul_z)
        cumul_z += (z2-z1)*s[1]

    # TODO
    if __UP in sides:
        a=0
        #render
    #... etc for all sides!


def __gen_bld_pyramid(rect, h):
    box_cnt = np.random.randint(settings.settings["bld_pyramid_box_cnt_min"], settings.settings["bld_pyramid_box_cnt_max"])

    zcoords = []
    widths = [1.]

    #long_side = max(abs(rect[0]-rect[2]), abs(rect[1]-rect[3]))
    short_side = min(abs(rect[0]-rect[2]), abs(rect[1]-rect[3]))

    for i in range(box_cnt - 1):
        zcoords.append(np.random.uniform(settings.settings["bld_sq_min"], h))

        # fraction of base size
        widths.append( np.random.uniform((np.random.uniform(settings.settings["bld_sq_min"])/short_side),
                                         1.-box_cnt*0.05 + i*0.05) )

    zcoords.sort()
    widths.sort(reverse=True)

    #print(zcoords)
    #print(widths)
    #print("bld")

    # generate boxes
    for idx,z in enumerate(zcoords):
        w_abs = short_side * widths[idx]
        segm_rect = (rect[0] + w_abs, rect[1] + w_abs, rect[2] - w_abs, rect[3] - w_abs)

        zprev = zcoords[idx-1]
        if idx == 0:
            zprev = 0

        model3d.cube_2dh(segm_rect, height=z*h, z=zprev)

        #__render_segm(segm_rect, zprev, z*h, __gen_bld_elem_style())

    # TODO facade decor (lines / stripes +++)
    # TODO generate roof decor


def __gen_bld_boxy(rect, h):
    return


def generate(bld_areas):
    for a in bld_areas:
        p = np.random.uniform()
        # TODO height map

        if p < settings.settings["bld_pyramid_prob"]:
            __gen_bld_pyramid(a, np.random.uniform(settings.settings["bld_h_min"], settings.settings["bld_h_max"]))
        else:
            __gen_bld_boxy(a, np.random.uniform(settings.settings["bld_h_min"], settings.settings["bld_h_max"]))
        # elif p < (settings["bld_pyramid_prob"]+settings["bld_boxy_prob"])


#generate([(1, 2, 2), (4, 5, 6)])