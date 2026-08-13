import sys
import colorsys
import math
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPolygonF, QRadialGradient
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget

class HSVWheel(QWidget):
    def __init__(self, size=400, angle_label_font_size=16, parent=None):
        super().__init__(parent)
        self.wheel_size = size
        self.angle_label_font_size = angle_label_font_size
        self.setMinimumSize(size + 120, size + 100)
        self.image = self.create_hsv_wheel(size)
        self.arrows = None
    def set_arrows(self, arrows):
        """
        arrow_data format:
            [
                ([lower_angle, higher_angle], saturation),
                ([lower_angle, higher_angle], saturation),
            ]

        angles are in degrees.
        saturation is 0.0 to 1.0.
        """

        self.arrows = arrows
        self.update()        

    def color_for_angle(self, angle_deg, saturation):
        hue = ((angle_deg % 360.0) / 360.0) % 1.0
        sat = max(0.0, min(1.0, saturation))
        val = 1.0
        red, green, blue = colorsys.hsv_to_rgb(hue, sat, val)
        return QColor(
            int(red * 255),
            int(green * 255),
            int(blue * 255)
        )
        
    def draw_arrow(self, painter, angle_deg, saturation,color):
        saturation = max(0.0, min(1.0, saturation))

        cx = self.width() / 2
        cy = self.height() / 2

        radius = min(self.width(), self.height()) / 2
        length = saturation * radius

        theta = math.radians(angle_deg)

        x2 = cx + length * math.cos(theta)
        y2 = cy - length * math.sin(theta)

        start = QPointF(cx, cy)
        end = QPointF(x2, y2)

        arrow_color = self.color_for_angle(angle_deg, saturation)
        outline = QPen(QColor(20, 20, 20, 170))
        outline.setWidth(7)
        outline.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(outline)
        painter.drawLine(start, end)

        pen = QPen(arrow_color)
        pen.setWidth(4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(start, end)

        # Arrow head
        head_size = 12
        angle1 = theta + math.radians(150)
        angle2 = theta - math.radians(150)

        p1 = QPointF(
            x2 + head_size * math.cos(angle1),
            y2 - head_size * math.sin(angle1)
        )

        p2 = QPointF(
            x2 + head_size * math.cos(angle2),
            y2 - head_size * math.sin(angle2)
        )

        arrow_head = QPolygonF([end, p1, p2])
        painter.setPen(QPen(QColor(20, 20, 20, 170), 2))
        painter.setBrush(arrow_color)
        painter.drawPolygon(arrow_head)    

    def create_hsv_wheel(self, size):
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        cx = size / 2
        cy = size / 2
        radius = size / 2

        for y in range(size):
            for x in range(size):
                dx = x - cx
                dy = y - cy

                r = (dx * dx + dy * dy) ** 0.5

                if r <= radius:
                    # Screen y increases downward; Vulkan velocity angles use
                    # Cartesian y-up coordinates.
                    hue = (math.atan2(-dy, dx) / (2 * math.pi)) % 1.0
                    sat = r / radius
                    val = 1.0

                    red, green, blue = colorsys.hsv_to_rgb(hue, sat, val)
                    image.setPixelColor(
                        x, y,
                        QColor(
                            int(red * 255),
                            int(green * 255),
                            int(blue * 255)
                        )
                    )
        return image

    def draw_wheel_finish(self, painter, wheel_rect):
        shadow = QRectF(wheel_rect)
        shadow.translate(8, 10)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 45))
        painter.drawEllipse(shadow)

        painter.drawImage(
            int(wheel_rect.x()),
            int(wheel_rect.y()),
            self.image
        )

        radius = wheel_rect.width() / 2
        gradient = QRadialGradient(
            QPointF(wheel_rect.x() + radius * 0.72, wheel_rect.y() + radius * 0.55),
            radius * 1.35,
            QPointF(wheel_rect.x() + radius * 0.52, wheel_rect.y() + radius * 0.38)
        )
        gradient.setColorAt(0.0, QColor(255, 255, 255, 120))
        gradient.setColorAt(0.38, QColor(255, 255, 255, 28))
        gradient.setColorAt(0.78, QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 58))

        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(70, 70, 70, 120), 2))
        painter.drawEllipse(wheel_rect)

        highlight = QRectF(wheel_rect)
        highlight.adjust(radius * 0.12, radius * 0.08, -radius * 0.30, -radius * 0.52)
        painter.setBrush(QColor(255, 255, 255, 45))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(highlight)

    def draw_angle_labels(self, painter, wheel_rect):
        center = wheel_rect.center()
        radius = wheel_rect.width() / 2
        painter.setFont(QFont("Consolas", self.angle_label_font_size))
        painter.setPen(QColor(255, 255, 255))

        for angle_deg, label in ((0, "0"), (90, "90"), (180, "180"), (270, "270")):
            theta = math.radians(angle_deg)
            label_radius = radius + 26
            pos = QPointF(
                center.x() + label_radius * math.cos(theta),
                center.y() - label_radius * math.sin(theta)
            )
            text_rect = QRectF(pos.x() - 32, pos.y() - 16, 64, 32)

            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        if self.arrows is not None:
            deg = self.arrows[0][0]           # first arrow angle
            rad = math.radians(deg)

            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Consolas", 11))

            painter.drawText(
                10, 20,
                f"DEG: {deg:6.1f}   RAD: {rad:7.4f}"
            )

        x = (self.width() - self.image.width()) // 2
        y = (self.height() - self.image.height()) // 2
        wheel_rect = QRectF(x, y, self.image.width(), self.image.height())

        self.draw_wheel_finish(painter, wheel_rect)
        self.draw_angle_labels(painter, wheel_rect)

        for low, high, sat, color in self.arrows or []:
            self.draw_arrow(painter, low, sat, color)
            self.draw_arrow(painter, high, sat, color)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.hsv_wheel = HSVWheel(400)
        self.tabs.addTab(self.hsv_wheel, "HSV Color Wheel")

        # Initial arrow
        self.angle = 45
        self.angleA = 360-45
        self.hsv_wheel.set_arrows([
            (self.angle, self.angle, 1.0, Qt.GlobalColor.black),
            (self.angleA, self.angleA, 1.0, Qt.GlobalColor.black)
        ])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_D:
            self.angle = (self.angle + 1) % 360

            self.hsv_wheel.set_arrows([
                (self.angle, self.angle, 1.0, Qt.GlobalColor.black)
            ])

        elif event.key() == Qt.Key.Key_A:
            self.angle = (self.angle - 1) % 360

            self.hsv_wheel.set_arrows([
                (self.angle, self.angle, 1.0, Qt.GlobalColor.black)
            ])
app = QApplication(sys.argv)
window = MainWindow()
window.resize(600, 500)
window.show()
sys.exit(app.exec())
