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
base_s = np.clip(r / RADIUS, 0, 1)

mask = r <= RADIUS


def make_image(h_offset, s_scale, value):

    h = (base_h + h_offset) % 1.0
    s = np.clip(base_s * s_scale, 0.0, 1.0)
    v = np.ones_like(s) * value

    hsv = np.dstack((h, s, v))
    rgb = hsv_to_rgb(hsv)

    rgb[~mask] = 1.0

    return rgb, h, s, v


fig, ax = plt.subplots(figsize=(8, 9))
plt.subplots_adjust(bottom=0.25)

rgb, H, S, V = make_image(0.0, 1.0, 1.0)

img = ax.imshow(rgb, origin='lower')
ax.axis('off')
ax.set_title("Interactive HSV Wheel")

marker, = ax.plot([], [], 'ko', markersize=10, fillstyle='none')

text = fig.text(
    0.02,
    0.02,
    "",
    fontsize=12
)

ax_h = plt.axes([0.15, 0.15, 0.7, 0.03])
ax_s = plt.axes([0.15, 0.10, 0.7, 0.03])
ax_v = plt.axes([0.15, 0.05, 0.7, 0.03])

slider_h = Slider(ax_h, "Hue Offset", 0.0, 1.0, valinit=0.0)
slider_s = Slider(ax_s, "Sat Scale", 0.0, 2.0, valinit=1.0)
slider_v = Slider(ax_v, "Value", 0.0, 1.0, valinit=1.0)


def redraw(val):
    global H, S, V

    rgb, H, S, V = make_image(
        slider_h.val,
        slider_s.val,
        slider_v.val
    )

    img.set_data(rgb)
    fig.canvas.draw_idle()


slider_h.on_changed(redraw)
slider_s.on_changed(redraw)
slider_v.on_changed(redraw)


def onclick(event):

    if event.inaxes != ax:
        return

    x = event.xdata - RADIUS
    y = event.ydata - RADIUS

    rr = np.sqrt(x*x + y*y)

    if rr > RADIUS:
        return

    marker.set_data([event.xdata], [event.ydata])

    ix = int(event.ydata)
    iy = int(event.xdata)

    h = H[ix, iy]
    s = S[ix, iy]
    v = V[ix, iy]

    rgb = hsv_to_rgb([[h, s, v]])[0]

    text.set_text(
        f"H = {h:.3f}\n"
        f"S = {s:.3f}\n"
        f"V = {v:.3f}\n"
        f"R = {rgb[0]:.3f}\n"
        f"G = {rgb[1]:.3f}\n"
        f"B = {rgb[2]:.3f}"
    )

    fig.canvas.draw_idle()


fig.canvas.mpl_connect('button_press_event', onclick)

plt.show()