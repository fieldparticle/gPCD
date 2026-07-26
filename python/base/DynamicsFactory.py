"""Select the Python dynamics class for a cfg file."""

from pathlib import Path

from gbase import libconf

from base.ForceDynamicsBase import ForceDynamics
from base.ForceDynamicsLighting import ForceDynamicsLighting


DYNAMICS_CLASS_REGISTRY = {
    "base": ForceDynamics,
    "fpm": ForceDynamics,
    "forcedynamics": ForceDynamics,
    "lighting": ForceDynamicsLighting,
    "fpml": ForceDynamicsLighting,
    "forcedynamicslighting": ForceDynamicsLighting,
}


def _normal_key(value):
    return str(value).strip().lower()


def dynamics_class_name_from_cfg(cfg_file_name):
    """Return the configured Python dynamics class name, or base by default."""
    cfg_path = Path(cfg_file_name)
    with cfg_path.open("r", encoding="utf-8") as cfg_file:
        cfg = libconf.load(cfg_file)

    configured_class = (
        cfg.get("python_dynamics_class")
        or cfg.get("dynamics_class")
        or cfg.get("python_dynamics")
    )
    if configured_class:
        return configured_class

    if (
        cfg.get("photon_periodic_recycle_enabled", False)
        or cfg.get("boundary_space_lighting_enabled", False)
    ):
        return "ForceDynamicsLighting"

    return "base"


def create_dynamics_for_cfg(cfg_file_name):
    """Create the configured dynamics object for a cfg file."""
    class_name = dynamics_class_name_from_cfg(cfg_file_name)
    dynamics_class = DYNAMICS_CLASS_REGISTRY.get(_normal_key(class_name))
    if dynamics_class is None:
        valid = ", ".join(sorted(DYNAMICS_CLASS_REGISTRY))
        raise ValueError(
            f"unknown Python dynamics class {class_name!r}; valid values: {valid}"
        )
    return dynamics_class()
