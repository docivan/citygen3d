import math
import numpy as np
import random
import cv2

import settings
import model3d

#encoding: (street_start, street_end) - in __HORIZ or __VERT coords, respectively
streets_x = []
streets_y = []

__HORIZ = 0
__VERT = 1
__UP = 0
__DOWN = 1

__img = []

#assumes dir = up => thus flip if not
def __gen_car_lane(x, y1, y2, w) : #, dir = __UP):
    # TODO follow exponential function
    # this means: generate grid, fill according to probability (exp)
    # then jitter by (0, car_max_w/w)
    # -- for loop with up to f.ex. 10 attempts at jitter, if fail = abandom

    cars = []
    #cur_y = y1
    #while True:

    # generate grid:
    car_slots = np.random.randint(0, 2, size=int(math.floor((y2-y1)/settings.settings["car_l_max"])))
    #print(car_slots)
    #print(w)

    for idx, val in enumerate(car_slots):
        if val:
            cars.append((
                (x - w/2., y1 + idx*settings.settings["car_l_max"]),
                (x + w/2., y1 + (idx+1)*settings.settings["car_l_max"])
            ))


    #for

    return cars

def __gen_car(bound_rect):
    # TODO - 3d
    model3d.cube_2dh((bound_rect[0][0], bound_rect[0][1], bound_rect[1][0], bound_rect[1][1]),
                     height=(bound_rect[1][0]-bound_rect[0][0])*settings.settings["car_h_ratio"])

    if settings.settings["debug"]:
        print(bound_rect)
        p1 = (int(bound_rect[0][0]), int(bound_rect[0][1]))
        p2 = (int(bound_rect[1][0]), int(bound_rect[1][1]))

        cv2.rectangle(__img, p1, p2, (random.randint(0, 254), random.randint(0, 254), random.randint(0, 254)), -1)

def __gen_st(rect, dir=__VERT):
    st_rect = rect

    if dir == __HORIZ: # flip x and y
        st_rect = ((rect[0][1], rect[0][0]), (rect[1][1], rect[1][0]))

    # TODO split rect into 2x number of lanes, x in each direction
    # TODO get settings from lane width and side walk params

    # for now, only 2 lanes no matter what
    midlane_div = (st_rect[1][0]-st_rect[0][0]) / 3.

    # TODO gen both up and down
    cars = __gen_car_lane(st_rect[0][0] + midlane_div, st_rect[0][1], st_rect[1][1], midlane_div/2.) + \
           __gen_car_lane(st_rect[0][0] + 2*midlane_div, st_rect[0][1], st_rect[1][1], midlane_div/2.)

    for car in cars:
        if dir == __HORIZ:  # flip x and y back
            car = ((car[0][1], car[0][0]), (car[1][1], car[1][0]))
        __gen_car(car)

def generate():
    print("Generating streets...")
    # TODO leave as global??
    global __img

    if settings.settings["debug"]:
        __img = np.zeros((int(settings.settings["height"]), int(settings.settings["width"]), 3), np.uint8)

    intersections = np.random.randint(0, 2, size=[len(streets_y), len(streets_x)])
    # these are lists of ((x1,y1), (x2,y2)) where (x1,y1) define min rect and (x2,y2) defines max rect
    v_st_rects = []

    for st_x in range(len(streets_x)):
        start = (streets_x[st_x][0], 0)

        for st_y in range(len(streets_y)):
            if intersections[st_x][st_y] == __HORIZ:
                v_st_rects.append((start, (streets_x[st_x][0] + streets_x[st_x][1], streets_y[st_y][0])))
                start = (streets_x[st_x][0], streets_y[st_y][0] + streets_y[st_y][1])

        # last one
        v_st_rects.append((start, (streets_x[st_x][0] + streets_x[st_x][1], settings.settings["height"])))

    h_st_rects = []

    for st_y in range(len(streets_y)):
        start = (0, streets_y[st_y][0])

        for st_x in range(len(streets_x)):
            if intersections[st_x][st_y] == __VERT:
                h_st_rects.append((start, (streets_x[st_x][0], streets_y[st_y][0] + streets_y[st_y][1])))
                start = (streets_x[st_x][0] + streets_x[st_x][1], streets_y[st_y][0])

        # last one
        h_st_rects.append((start, (settings.settings["width"], streets_y[st_y][0] + streets_y[st_y][1])))

    if settings.settings["debug"]:
        for v in v_st_rects + h_st_rects:
            col = random.randint(50, 254)
            cv2.rectangle(__img, v[0], v[1], (col,col,col), -1)

    for v in v_st_rects:
        __gen_st(v, dir=__VERT)

    for h in h_st_rects:
        __gen_st(h, dir=__HORIZ)

    if settings.settings["debug"]:
        cv2.imwrite("streets.png", __img)