import random
import numpy as np
import math

import settings
import model3d
import utils


def gen_tree(rect, z):
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
        model3d.cone((x, y, z), diameter,
                     np.random.uniform(settings.settings["tree_sz_min"], settings.settings["tree_sz_max"]))
    else:
        model3d.sphere_cubed((x, y, z+diameter / 2. * 1.5), diameter, ratio = 1./3./2.)
        #trunk
        s = diameter/2. - diameter/3./2.
        model3d.cube_2v((x-s,y-s,z), (x+s,y+s,z+diameter/4.))

    #if settings.settings["debug"]:
        #cv2.circle(img, (int(x), int(y)), int(diameter / 2), (0, 0, 0), thickness=1)


#z != 0 means roof garden
def gen_park(rect, z=0):
    potential_trees = utils.split_rect(rect, settings.settings["tree_sz_min"], settings.settings["tree_sz_max"])

    fill = random.uniform(settings.settings["tree_fill_min"], settings.settings["tree_fill_max"])
    if z != 0:
        fill = 1

    tree_cnt = int(math.floor(len(potential_trees) * fill))

    for i in range(tree_cnt):
        idx = random.randint(0, len(potential_trees) - 1)
        gen_tree(potential_trees[idx], z)
        potential_trees.pop(idx)