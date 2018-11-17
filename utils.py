import numpy as np
import random
import math


def distrib_exp(falloff = 100, cutoff = 0.1):
    # TODO cutoff!
    # TODO cutoff for both sides??
    return 1 - (pow(falloff, np.random.uniform()) - 1) / (falloff - 1)


# TODO falloff + cutoff!
def random_exp(lo, hi, falloff = 100):
    return lo + distrib_exp(falloff=falloff) * (hi-lo)


def geom_dist(v1, v2):
    return math.sqrt((v1[0]-v2[0])*(v1[0]-v2[0]) + (v1[1]-v2[1])*(v1[1]-v2[1]))

def cmp_float(f1, f2, error=0.0001):
    if math.fabs(f1 - f2) < error:
        return True
    else:
        return False


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
        for split_line in range(round(min_w), round(h - min_w + 1)):
            rect1 = (rect[0], rect[1], rect[2], rect[1] + split_line)
            rect2 = (rect[0], rect[1] + split_line, rect[2], rect[3])
            possible_rects.append([rect1, rect2])

    if w >= (min_w * 2):
        for split_line in range(round(min_w), round(w - min_w + 1)):
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