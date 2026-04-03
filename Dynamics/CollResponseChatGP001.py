"""
Two-sphere collision response (3D) with:
  1) Rigid impulse (restitution + optional Coulomb friction) AND
  2) Optional positional correction for penetration (Baumgarte-style)

This is a practical, game/DEM-friendly "instantaneous" contact response.
If you want a soft-sphere (spring-damper / Hertz) time-stepping model, say so.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class Sphere:
    x: np.ndarray  # position (3,)
    v: np.ndarray  # velocity (3,)
    m: float       # mass
    r: float       # radius

    def __post_init__(self):
        self.x = np.asarray(self.x, dtype=float).reshape(3)
        self.v = np.asarray(self.v, dtype=float).reshape(3)
        if self.m <= 0:
            raise ValueError("Mass must be positive.")
        if self.r <= 0:
            raise ValueError("Radius must be positive.")


def collide_spheres(
    a: Sphere,
    b: Sphere,
    restitution: float = 0.5,
    friction: float = 0.0,
    pos_correction: bool = True,
    percent: float = 0.8,   # fraction of penetration to correct
    slop: float = 1e-6      # penetration allowed before correction
) -> tuple[Sphere, Sphere, dict]:
    """
    Resolves collision between two spheres if they overlap or are closing.

    Parameters
    ----------
    restitution : e in [0,1]
      0 = perfectly inelastic, 1 = perfectly elastic
    friction : mu >= 0
      Coulomb friction coefficient for tangential impulse (simple model)
    pos_correction : bool
      Apply positional correction to remove overlap (helps stability)
    percent, slop
      Baumgarte-style correction parameters.

    Returns
    -------
    updated spheres (a, b) and debug info
    """
    e = float(np.clip(restitution, 0.0, 1.0))
    mu = float(max(0.0, friction))

    # Relative position
    r_ab = a.x - b.x
    dist = float(np.linalg.norm(r_ab))

    # Handle coincident centers robustly
    if dist < 1e-12:
        # Pick an arbitrary normal
        n = np.array([1.0, 0.0, 0.0], dtype=float)
        dist = 0.0
    else:
        n = r_ab / dist  # contact normal points from b -> a

    # Penetration depth
    penetration = (a.r + b.r) - dist

    # Relative velocity
    v_rel = a.v - b.v
    v_rel_n = float(np.dot(v_rel, n))  # normal relative speed

    # If not overlapping and not closing, do nothing
    if penetration <= 0.0 and v_rel_n >= 0.0:
        return a, b, {
            "collided": False,
            "penetration": penetration,
            "v_rel_n": v_rel_n,
            "impulse_n": 0.0,
            "impulse_t": 0.0
        }

    inv_ma = 1.0 / a.m
    inv_mb = 1.0 / b.m
    inv_mass_sum = inv_ma + inv_mb

    # --- Normal impulse (rigid, instantaneous) ---
    # If they're separating but still overlapped, treat normal speed as 0 to avoid "pulling together"
    closing_speed = min(v_rel_n, 0.0)

    # jn >= 0 pushes them apart
    jn = -(1.0 + e) * closing_speed / inv_mass_sum

    # Apply normal impulse
    impulse_n = jn * n
    a.v = a.v + impulse_n * inv_ma
    b.v = b.v - impulse_n * inv_mb

    jt = 0.0

    # --- Tangential (friction) impulse (Coulomb clamp) ---
    if mu > 0.0:
        # Recompute relative velocity after normal impulse
        v_rel2 = a.v - b.v

        # Tangential component
        v_t = v_rel2 - np.dot(v_rel2, n) * n
        v_t_norm = float(np.linalg.norm(v_t))

        if v_t_norm > 1e-12:
            t = v_t / v_t_norm

            # Desired tangential impulse to cancel tangential relative velocity (no rotation here)
            jt_unc = -np.dot(v_rel2, t) / inv_mass_sum

            # Coulomb limit
            jt = float(np.clip(jt_unc, -mu * jn, mu * jn))

            impulse_t = jt * t
            a.v = a.v + impulse_t * inv_ma
            b.v = b.v - impulse_t * inv_mb

    # --- Positional correction to remove penetration (prevents stacking drift) ---
    if pos_correction and penetration > slop:
        corr_mag = percent * (penetration - slop) / inv_mass_sum
        corr = corr_mag * n
        a.x = a.x + corr * inv_ma
        b.x = b.x - corr * inv_mb

    return a, b, {
        "collided": True,
        "penetration": penetration,
        "v_rel_n": v_rel_n,
        "impulse_n": float(jn),
        "impulse_t": float(jt),
        "normal": n.copy()
    }


if __name__ == "__main__":
    # Example usage
    A = Sphere(x=[0.0, 0.0, 0.0], v=[2.0, 0.2, 0.0], m=1.0, r=0.5)
    B = Sphere(x=[0.8, 0.0, 0.0], v=[0.0, 0.0, 0.0], m=2.0, r=0.5)

    A2, B2, info = collide_spheres(
        A, B,
        restitution=0.8,
        friction=0.2,
        pos_correction=True
    )

    print("Info:", info)
    print("A pos, vel:", A2.x, A2.v)
    print("B pos, vel:", B2.x, B2.v)