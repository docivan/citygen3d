import numpy as np
import math

import settings
import model3d
import parks
import utils

__UP = 1
__DOWN = 2
__LEFT = 3
__RIGHT = 4


def __gen_antenna(rect, z):

    pos = np.random.randint(1,5)

    xq = (rect[2]-rect[0])/4.
    yq = (rect[3]-rect[1])/4.

    if xq < (settings.settings["bld_roof_ant_d"]/2.) or yq < (settings.settings["bld_roof_ant_d"]/2.):
        return

    c = [rect[0] - settings.settings["bld_roof_ant_d"]/2., rect[1] - settings.settings["bld_roof_ant_d"]/2.]
    h = np.random.uniform(settings.settings["bld_roof_ant_h_min"], settings.settings["bld_roof_ant_h_max"])

    if pos == 1:
        c[0] += xq
        c[1] += yq
    elif pos == 2:
        c[0] += xq * 3
        c[1] += yq
    elif pos == 3:
        c[0] += xq * 3
        c[1] += yq * 3
    elif pos == 4:
        c[0] += xq
        c[1] += yq * 3
    else:
        c[0] += xq * 2
        c[1] += yq * 2

    c.append(c[0] + settings.settings["bld_roof_ant_d"])
    c.append(c[1] + settings.settings["bld_roof_ant_d"])
    model3d.cube_2dh(c, height=h, z=z)


def __gen_roof_decor(roof_rect, z):
    if np.random.uniform() < settings.settings["bld_roof_ant_prob"]:
        __gen_antenna(roof_rect, z)
        return

    if np.random.uniform() < settings.settings["bld_roof_cone_prob"]:
        # TODO this should really use the actual rect as directed by style!
        model3d.pyramid([roof_rect[0] + (roof_rect[2] - roof_rect[0]) * settings.settings["bld_pyramid_step_max"],
                         roof_rect[1] + (roof_rect[3] - roof_rect[1]) * settings.settings["bld_pyramid_step_max"],
                         roof_rect[2] - (roof_rect[2] - roof_rect[0]) * settings.settings["bld_pyramid_step_max"],
                         roof_rect[3] - (roof_rect[3] - roof_rect[1]) * settings.settings["bld_pyramid_step_max"]],
                        z*settings.settings["bld_roof_cone_h_ratio"], z=z)
        return

    treespaces = math.floor((roof_rect[2] - roof_rect[0]) / settings.settings["tree_sz_max"]) *\
                 math.floor((roof_rect[3] - roof_rect[1]) / settings.settings["tree_sz_max"])

    if treespaces>=4 and np.random.uniform() < settings.settings["bld_roof_garden_prob"]:
        parks.gen_park(roof_rect, z=z)




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

    short_side = min(abs(rect[0] - rect[2]), abs(rect[1] - rect[3]))
    cumul_z = z1

    max_offset = 0
    max_offset_rect = []

    for s in style:
        w_abs = short_side * s[0]
        segm_rect = list(rect)

        if __UP in sides:
            segm_rect[3] -= w_abs
        if __DOWN in sides:
            segm_rect[1] += w_abs
        if __LEFT in sides:
            segm_rect[0] += w_abs
        if __RIGHT in sides:
            segm_rect[2] -= w_abs

        model3d.cube_2dh(segm_rect, height=(z2-z1)*s[1], z=cumul_z)

        #this basically finds the main block of the building segment for decor drawing elsewhere
        if w_abs > max_offset:
            max_offset = w_abs
            max_offset_rect = [segm_rect[0], segm_rect[1], cumul_z, segm_rect[2], segm_rect[3], cumul_z + (z2-z1)*s[1]]

        cumul_z += (z2-z1)*s[1]

    # facade decor:
    if np.random.uniform() < settings.settings["bld_facade_stripes_prob"]:
        facade_type = np.random.randint(0, 4)  # 0 - SN vert, 1 - EW vert, 2 - both vert, 3 - horiz (all walls)

        #vert south + north
        if facade_type==0 or facade_type==2:
            stripe_cnt = np.random.randint(settings.settings["bld_facade_stripes_min"],
                                           settings.settings["bld_facade_stripes_max"])
            stripe_w = (max_offset_rect[3] - max_offset_rect[0]) / (stripe_cnt*2+1)

            for i in range(stripe_cnt):
                x = max_offset_rect[0] + stripe_w + stripe_w*2*i
                model3d.cube_2dh(
                    [x, rect[1], x + stripe_w, max_offset_rect[1]],
                    height=(max_offset_rect[5]-max_offset_rect[2]), z = max_offset_rect[2])
                model3d.cube_2dh(
                    [x, max_offset_rect[4], x + stripe_w, rect[3]],
                    height=(max_offset_rect[5] - max_offset_rect[2]), z=max_offset_rect[2])

        #vert east + west
        if facade_type == 1 or facade_type == 2:
            stripe_cnt = np.random.randint(settings.settings["bld_facade_stripes_min"],
                                           settings.settings["bld_facade_stripes_max"])
            stripe_w = (max_offset_rect[4] - max_offset_rect[1]) / (stripe_cnt * 2 + 1)

            for i in range(stripe_cnt):
                y = max_offset_rect[1] + stripe_w + stripe_w * 2 * i
                model3d.cube_2dh(
                    [rect[0], y, max_offset_rect[0], y + stripe_w],
                    height=(max_offset_rect[5] - max_offset_rect[2]), z=max_offset_rect[2])
                model3d.cube_2dh(
                    [max_offset_rect[3], y, rect[2], y + stripe_w],
                    height=(max_offset_rect[5] - max_offset_rect[2]), z=max_offset_rect[2])

        # horiz
        if facade_type == 3:
            if max_offset_rect[5] - max_offset_rect[2] < (settings.settings["bld_sq_min"]*5):
                return

            stripe_cnt = np.random.randint(settings.settings["bld_facade_stripes_min"]*2,
                                           settings.settings["bld_facade_stripes_max"]*2)
            stripe_w = (max_offset_rect[5] - max_offset_rect[2]) / (stripe_cnt * 2 + 1)

            if stripe_w < settings.settings["bld_sq_min"]:
                stripe_cnt = math.floor((max_offset_rect[5] - max_offset_rect[2]) / settings.settings["bld_sq_min"])
                stripe_w = (max_offset_rect[5] - max_offset_rect[2]) / (stripe_cnt * 2 + 1)

            for i in range(stripe_cnt):
                z = max_offset_rect[2] + stripe_w + stripe_w * 2 * i
                model3d.cube_2dh([rect[0], rect[1], rect[2], max_offset_rect[1]], height=stripe_w, z=z)
                model3d.cube_2dh([rect[0], max_offset_rect[4], rect[2], rect[3]], height=stripe_w, z=z)
                model3d.cube_2dh([rect[0], max_offset_rect[1], max_offset_rect[0], max_offset_rect[4]],
                                 height=stripe_w, z=z)
                model3d.cube_2dh([max_offset_rect[3], max_offset_rect[1], rect[2], max_offset_rect[4]],
                                 height=stripe_w, z=z)




def __gen_bld_pyramid(rect, h):
    box_cnt = np.random.randint(settings.settings["bld_pyramid_box_cnt_min"], settings.settings["bld_pyramid_box_cnt_max"])

    zcoords = []
    widths = []

    short_side = min(abs(rect[0]-rect[2]), abs(rect[1]-rect[3]))

    for i in range(box_cnt):
        z = utils.random_exp(settings.settings["bld_sq_min"], h)
        w = 0

        if i != 0:
            w = widths[i-1]

        w += utils.random_exp(0, settings.settings["bld_pyramid_step_max"])

        zcoords.append(z)
        widths.append(w)

    zcoords.sort()

    # generate boxes
    cumul_step = 0
    for idx,z in enumerate(zcoords):
        cumul_step += widths[idx]
        w_abs = short_side * cumul_step / 2

        segm_rect = (rect[0] + w_abs, rect[1] + w_abs, rect[2] - w_abs, rect[3] - w_abs)

        zprev = zcoords[idx-1]
        if idx == 0:
            zprev = 0

        style = __gen_bld_elem_style()
        __render_segm(segm_rect, zprev, z, style)

    # best option would to code function __get_style_elem_rects (base_rect, style, elem_id)
    # OR just save the last segm highest offset in the loop above
    __gen_roof_decor(segm_rect, zcoords[-1])

    # TODO facade decor (lines / stripes +++)
    # -- helipad?
    # TODO garden!

def generate(bld_areas):
    print("Generating buildings...")
    for idx, a in enumerate(bld_areas):
        print("- building", idx+1, "of", len(bld_areas))

        # simply minx, miny
        max_h = settings.settings["bld_h_max"]

        for p in settings.settings["height_hot_spots"]:
            dist = utils.geom_dist(a[0:2], p[0])

            if dist < p[2]:
                max_h += p[1] * dist / p[2]

        __gen_bld_pyramid(a, np.random.uniform(settings.settings["bld_h_min"], max_h))
