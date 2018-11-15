import numpy as np
import settings

__UP = 1
__DOWN = 2
__LEFT = 3
__RIGHT = 4


def __gen_roof_decor(roof_rect):
    #TODO
    return


# ((ratio, h_ratio))
# all relative
def __gen_bld_elem_style():
    style = []

    base = 0
    top1 = 0
    top2 = 0

    if np.random.uniform() < settings.settings["bld_boxy_base_prob"]:
        base = np.random.uniform(0, settings.settings["bld_boxy_base_h_max"])
    if np.random.uniform() < settings.settings["bld_boxy_top1_prob"]:
        top1 = np.random.uniform(0, settings.settings["bld_boxy_top1_h_max"])

        if np.random.uniform() < settings.settings["bld_boxy_top2_prob"]:
            top2 = np.random.uniform(0, settings.settings["bld_boxy_top2_h_max"])

    mid = 1 - (base + top1 + top2)

    if base > 0:
        style.append((1., base))
        style.append((np.random.uniform(0, settings.settings["bld_boxy_base_step_max"]), mid))
    else:
        style.append((1., mid))

    if top1 > 0:
        if top2 > 0:

            top2_offset = np.random.uniform((0, (top1-top2)))
            #top1_ratio =

            style.append((np.random.uniform(0, settings.settings["bld_boxy_top1_step_max"]), top2_offset))
            style.append((np.random.uniform(0, settings.settings["bld_boxy_top2_step_max"]), top2))
            style.append((np.random.uniform(0, settings.settings["bld_boxy_top1_step_max"]), top1 - top2 - top2_offset))
        else:
            style.append((np.random.uniform(0, settings.settings["bld_boxy_top1_step_max"]), top1))

    return style


def __render_bld(base_rect, z1, z2, style, sides=(__UP, __DOWN, __LEFT, __RIGHT)):
    assert len(sides) > 0
    assert len(sides) <= 4

    # TODO

    return


def __gen_bld_pyramid(rect, h):
    box_cnt = np.random.randint(settings.settings["bld_pyramid_box_cnt_min"], settings.settings["bld_pyramid_box_cnt_max"])

    zcoords = []
    widths = []

    for i in range(box_cnt - 1):
        zcoords.append(np.random.uniform(settings.settings["bld_sq_min"], h))
        widths.append(np.random.uniform())  # fraction of base size

    zcoords.sort()
    widths.sort(reverse=True)

    # generate boxes
    # TODO should be in a sep. function: facade decor (lines / stripes / ledges +++)
    __render_bld((1, 2, 3), 0, 10, __gen_bld_elem_style())

    # generate roof decor

    return


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