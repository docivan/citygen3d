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


def cmp_float(f1, f2, error=0.01):
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
    v2 = (rect[2], rect[3], height)

    cube_2v(v1, v2)


def sphere(c, d, subdiv_xy=10, subdiv_z=5):
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


def cone(c, r1, h, r2=0, subdiv=10):
    # TODO
    return 0


def cylinder(c, r, h, subdiv=10):
    cone(c, r, h, r2=r, subdiv=subdiv)

# stlfile = init("test.stl")
# cube2v((-1,-1,-1), (1,1,1))
# cube2v((1,1,1), (-1,-1,-1))
# cube_2dh((-1,-1, 1,1), height=4)
# sphere((1,1,1), 2)
# sphere((0,0,0), 2)
# cylinder((0,0,0), 2, 5)
# deinit(stlfile)
