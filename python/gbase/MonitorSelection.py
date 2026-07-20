import ctypes
from pathlib import Path

import libconf


def load_preferred_monitor(default=0):
    cfg_file = Path(__file__).resolve().parents[1] / "ParticleUtil.cfg"
    if not cfg_file.exists():
        return int(default)
    try:
        with cfg_file.open("r", encoding="utf-8") as handle:
            cfg = libconf.load(handle)
        return int(cfg.get("preferred_monitor", default))
    except (OSError, TypeError, ValueError):
        return int(default)


def monitor_bounds():
    bounds = []

    if hasattr(ctypes, "windll"):
        user32 = ctypes.windll.user32

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        MONITORENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(RECT),
            ctypes.c_double,
        )

        def callback(_monitor, _dc, rect, _data):
            bounds.append(
                (
                    int(rect.contents.left),
                    int(rect.contents.top),
                    int(rect.contents.right),
                    int(rect.contents.bottom),
                )
            )
            return 1

        user32.EnumDisplayMonitors(0, 0, MONITORENUMPROC(callback), 0)

    return bounds


def preferred_monitor_rect(default_index=0):
    bounds = monitor_bounds()
    if not bounds:
        return None
    index = load_preferred_monitor(default_index)
    if index < 0:
        index = 0
    if index >= len(bounds):
        index = len(bounds) - 1
    return bounds[index]


def preferred_window_position(window_width=0, window_height=0, margin=0):
    rect = preferred_monitor_rect()
    if rect is None:
        return None
    left, top, right, bottom = rect
    width = max(0, int(window_width))
    height = max(0, int(window_height))
    x = left + int(margin)
    y = top + int(margin)
    if width > 0:
        x = min(x, max(left, right - width))
    if height > 0:
        y = min(y, max(top, bottom - height))
    return x, y
