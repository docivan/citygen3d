import math
import numpy as np

stlfile = None


def init(filename):
    global stlfile

    if is_init():
        deinit()

    stlfile = open(filename, "w")
    stlfile.write("solid {}\n".format(filename))
    return stlfile


def is_init():
    if stlfile is None:
        return False

    return True


def deinit():
    global stlfile

    stlfile.write("endsolid {}\n".format(stlfile.name))
    stlfile.close()

    stlfile = None


def ck_valid_pt(*pt, dim):
    for p in pt:
        if len(p) == dim:
            for i in p:
                if not isinstance(i, (int, float)):
                    return False

            return True
        else:
            return False


def cmp_float(f1, f2, error=0.0001):
    if math.fabs(f1 - f2) < error:
        return True
    else:
        return False


def cmp_pt(v1, v2, error=0.01):
    assert len(v1) == len(v2)

    for i in range(len(v1)):
        if not cmp_float(v1[i], v2[i]):
            return False

    return True


def calc_normal(v1, v2, v3):
    # u = v2 - v1
    u = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])

    # v = v3 - v1
    v = (v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2])

    # n = u x v
    # Nx = UyVz - UzVy
    # Ny = UzVx - UxVz
    # Nz = UxVy - UyVx
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])

    return n


# NB! all are CCW!
def triangle(v1, v2, v3):
    assert ck_valid_pt(v1, v2, v3, dim=3)

    normal = calc_normal(v1, v2, v3)
    stlfile.write("facet normal {} {} {}\n".format(normal[0], normal[1], normal[2]))
    stlfile.write("\touter loop\n")
    stlfile.write("\t\tvertex {} {} {}\n".format(v1[0], v1[1], v1[2]))
    stlfile.write("\t\tvertex {} {} {}\n".format(v2[0], v2[1], v2[2]))
    stlfile.write("\t\tvertex {} {} {}\n".format(v3[0], v3[1], v3[2]))
    stlfile.write("\tendloop\n")
    stlfile.write("endfacet\n")


def quad(v1, v2, v3, v4):
    triangle(v1, v2, v3)
    triangle(v1, v3, v4)


def cube(v):
    assert len(v) == 8
    quad(v[0], v[3], v[2], v[1])  # btm
    quad(v[4], v[5], v[6], v[7])  # top
    quad(v[0], v[4], v[7], v[3])
    quad(v[3], v[7], v[6], v[2])
    quad(v[1], v[2], v[6], v[5])
    quad(v[0], v[1], v[5], v[4])


def cube_2v(v1, v2):
    # recode:
    vmin = (min(v1[0], v2[0]), min(v1[1], v2[1]), min(v1[2], v2[2]))
    vmax = (max(v1[0], v2[0]), max(v1[1], v2[1]), max(v1[2], v2[2]))

    v = []

    # btm
    v.append(vmin)
    v.append((vmax[0], vmin[1], vmin[2]))
    v.append((vmax[0], vmax[1], vmin[2]))
    v.append((vmin[0], vmax[1], vmin[2]))

    # top
    v.append((vmin[0], vmin[1], vmax[2]))
    v.append((vmax[0], vmin[1], vmax[2]))
    v.append(vmax)
    v.append((vmin[0], vmax[1], vmax[2]))

    cube(v)


# takes a 2d base rect and a height
def cube_2dh(rect, height=1, z=0):
    assert len(rect) == 4

    v1 = (rect[0], rect[1], z)
    v2 = (rect[2], rect[3], z+height)

    cube_2v(v1, v2)


def sphere(c, d, subdiv_xy=10, subdiv_z=5):
    assert subdiv_xy >= 3
    assert subdiv_z >= 1
    assert ck_valid_pt(c, dim=3)
    r = d / 2.

    zsubdiv = np.linspace(0, math.pi, subdiv_z + 1, endpoint=False)[1:]

    xyvals = []
    zvals = []

    for radz in zsubdiv:
        zvals.append(c[2] + r * math.cos(radz))

        z_radius = r * math.sin(radz)
        xyvals_local = []

        for radxy in np.linspace(0, 2 * math.pi, subdiv_xy, endpoint=False):
            xyvals_local.append(
                (c[0] + z_radius * math.cos(radxy), c[1] + z_radius * math.sin(radxy))
            )

        xyvals.append(xyvals_local)

    # now stitching it all together:
    for i in range(subdiv_z - 1):
        for j in range(-1, subdiv_xy - 1):
            quad((xyvals[i + 1][j][0], xyvals[i + 1][j][1], zvals[i + 1]),
                 (xyvals[i + 1][j + 1][0], xyvals[i + 1][j + 1][1], zvals[i + 1]),
                 (xyvals[i][j + 1][0], xyvals[i][j + 1][1], zvals[i]),
                 (xyvals[i][j][0], xyvals[i][j][1], zvals[i])
                 )

    # finally, closing poles
    # potentially, could have used cones for this...
    top = (c[0], c[1], c[2] + r)
    btm = (c[0], c[1], c[2] - r)

    for j in range(-1, subdiv_xy - 1):
        triangle((xyvals[-1][j + 1][0], xyvals[-1][j + 1][1], zvals[-1]),
                 (xyvals[-1][j][0], xyvals[-1][j][1], zvals[-1]),
                 btm
                 )
        triangle(top,
                 (xyvals[0][j][0], xyvals[0][j][1], zvals[0]),
                 (xyvals[0][j + 1][0], xyvals[0][j + 1][1], zvals[0])
                 )


#all primitives below are generated flat in xy plane!

#generates a circle on the xy plane
def __circle2d_xy(c, d, subdiv=10, invert = False):
    assert  subdiv>=3

    r = d/2.

    points = []
    for radians in np.linspace(0, 2 * math.pi, subdiv, endpoint=False):
        points.append((c[0] + r * math.cos(radians), c[1] + r * math.sin(radians), c[2]))

    for idx in range(len(points)):
        if invert:
            triangle(points[idx-1], points[idx], c)
        else:
            triangle(points[idx], points[idx - 1], c)

    return points


def truncated_cone(c, d1, d2, h, subdiv = 10):
    lower = __circle2d_xy(c, d1, subdiv=subdiv)
    upper = __circle2d_xy((c[0], c[1], c[2]+h), d2, subdiv=subdiv, invert=True) # invert btm

    for i in range(subdiv):
        quad(lower[i-1], lower[i], upper[i], upper[i-1])


def cone(c, d, h, subdiv=10):
    base = __circle2d_xy(c, d, subdiv=subdiv, invert = True) # invert btm

    for i in range(subdiv):
        triangle(base[i-1], base[i], (c[0], c[1], c[2]+h))


def cylinder(c, d, h, subdiv=10):
    truncated_cone(c, d, d, h, subdiv=subdiv)


#this is a stylistic choice, and to avoid the slicing hell of overlapping geometry
#(or programming mesh booleans ops)
def sphere_cubed(c, d, ratio = 1./3.):
    inset = d * ratio
    main = d * (1 - ratio*2)

    z1 = c[2] - d/2.
    z2 = z1 + inset
    z3 = z2 + main
    z4 = c[2] + d/2.

    x_min = c[0] - d/2.
    x_max = c[0] + d/2.
    y_min = c[1] - d/2.
    y_max = c[1] + d/2.

    x_inset_min = x_min + inset
    x_inset_max = x_max - inset
    y_inset_min = y_min + inset
    y_inset_max = y_max - inset

    cube([
        (x_inset_min, y_inset_min, z1),
        (x_inset_max, y_inset_min, z1),
        (x_inset_max, y_inset_max, z1),
        (x_inset_min, y_inset_max, z1),

        (x_min, y_min, z2),
        (x_max, y_min, z2),
        (x_max, y_max, z2),
        (x_min, y_max, z2)])

    cube_2v((x_min, y_min, z2), (x_max, y_max, z3))

    cube([
        (x_min, y_min, z3),
        (x_max, y_min, z3),
        (x_max, y_max, z3),
        (x_min, y_max, z3),

        (x_inset_min, y_inset_min, z4),
        (x_inset_max, y_inset_min, z4),
        (x_inset_max, y_inset_max, z4),
        (x_inset_min, y_inset_max, z4)
        ])







# stlfile = init("test.stl")
# cube2v((-1,-1,-1), (1,1,1))
# cube2v((1,1,1), (-1,-1,-1))
# cube_2dh((-1,-1, 1,1), height=4)
# sphere((1,1,1), 2)
# sphere((0,0,0), 2)
# cylinder((0,0,0), 2, 5)
# deinit(stlfile)

# geom testing
#model3d.sphere((-10,-10,-10), 10, subdiv_xy=3, subdiv_z=1)
#model3d.cylinder((-5,-10,-10), 10, 5)
#model3d.cone((-25,-10,-10), 10, 5)
#model3d.truncated_cone((-50,-10,-10), 10, 5, 5)
#model3d.cube([(-75,-10,-10), (-80,-10,-10), (-80,-5,-10), (-75,-5,-10),
#              (-76,-9, -5), (-79, -9, -5), (-79, -6, -5), (-76, -6, -5)])