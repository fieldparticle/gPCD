import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
from matplotlib.widgets import Slider

SIZE = 700
RADIUS = SIZE // 2

y, x = np.ogrid[-RADIUS:RADIUS, -RADIUS:RADIUS]
r = np.sqrt(x**2 + y**2)
theta = np.arctan2(y, x)

base_h = (theta + np.pi) / (2 * np.pi)
base_s = np.clip(r / RADIUS, 0.0, 1.0)
mask = r <= RADIUS


def hsv_wheel(sat_scale, value):
    h = base_h
    s = np.clip(base_s * sat_scale, 0.0, 1.0)
    v = np.ones_like(s) * value

    hsv = np.dstack((h, s, v))
    rgb = hsv_to_rgb(hsv)
    rgb[~mask] = 1.0
    return rgb


def hue_strip(sat, value, n=4096, height=100):
    h = np.linspace(0.0, 1.0, n)
    s = np.ones_like(h) * sat
    v = np.ones_like(h) * value

    hsv = np.stack((h, s, v), axis=1)
    rgb = hsv_to_rgb(hsv)

    return np.tile(rgb[np.newaxis, :, :], (height, 1, 1))


fig = plt.figure(figsize=(10, 9))

ax_wheel = plt.axes([0.08, 0.38, 0.5, 0.5])
ax_strip = plt.axes([0.08, 0.25, 0.84, 0.08])

ax_sat = plt.axes([0.18, 0.15, 0.65, 0.03])
ax_val = plt.axes([0.18, 0.09, 0.65, 0.03])

wheel_img = ax_wheel.imshow(hsv_wheel(1.0, 1.0), origin="lower")
ax_wheel.axis("off")
ax_wheel.set_title("HSV Wheel")

strip_img = ax_strip.imshow(
    hue_strip(sat=1.0, value=1.0),
    aspect="auto",
    extent=[0, 360, 0, 1]
)

ax_strip.set_yticks([])
ax_strip.set_xlim(0, 360)
ax_strip.set_xlabel("Hue angle, degrees")
ax_strip.set_title("Full 0–360° Hue Strip")

ax_strip.set_xticks(np.arange(0, 361, 30))

slider_sat = Slider(ax_sat, "Saturation", 0.0, 1.0, valinit=1.0)
slider_val = Slider(ax_val, "Value", 0.0, 1.0, valinit=1.0)


def update(_):
    sat = slider_sat.val
    value = slider_val.val

    wheel_img.set_data(hsv_wheel(sat, value))
    strip_img.set_data(hue_strip(sat, value))

    fig.canvas.draw_idle()


slider_sat.on_changed(update)
slider_val.on_changed(update)

plt.show()