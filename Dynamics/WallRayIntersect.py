import numpy as np

def intersect_ray_line_2d(P, v, A, d):
    """
    Ray: R(t) = P + t*v
    Line: L(s) = A + s*d
    Returns (t, s, point) or None if parallel or no intersection.
    """

    v = np.array(v, dtype=float)
    d = np.array(d, dtype=float)
    P = np.array(P, dtype=float)
    A = np.array(A, dtype=float)

    # 2D cross product (scalar)
    def cross2(a, b):
        return a[0]*b[1] - a[1]*b[0]

    denom = cross2(v, d)
    if abs(denom) < 1e-12:
        return None  # parallel or coincident

    t = cross2((A - P), d) / denom
    s = cross2((A - P), v) / denom

    point = P + t * v
    return t, s, point


P = (0, 0)
v = (1, 1)
A = (1, 0)
d = (0, 1)

print(intersect_ray_line_2d(P, v, A, d))