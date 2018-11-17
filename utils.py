import numpy as np


def distrib_exp(falloff = 100, cutoff = 0.1):
    # TODO cutoff!
    # TODO cutoff for both sides??
    return 1 - (pow(falloff, np.random.uniform()) - 1) / (falloff - 1)


# TODO falloff + cutoff!
def random_exp(lo, hi, falloff = 100):
    return lo + distrib_exp(falloff=falloff) * (hi-lo)