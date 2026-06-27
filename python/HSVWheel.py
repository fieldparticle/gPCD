import sys
import colorsys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QImage
from PyQt6.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QMainWindow
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPen, QPainterPath, QPolygonF
import math

class HSVWheel(QWidget):
    def __init__(self, size=400, parent=None):
        super().__init__(parent)
        self.wheel_size = size
        self.setMinimumSize(size, size)
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
        
    def draw_arrow(self, painter, angle_deg, saturation,color):
        saturation = max(0.0, min(1.0, saturation))

        cx = self.width() / 2
        cy = self.height() / 2

        radius = min(self.width(), self.height()) / 2
        length = saturation * radius

        theta = math.radians(angle_deg)

        x2 = cx + length * math.cos(theta)
        y2 = cy + length * math.sin(theta)

        start = QPointF(cx, cy)
        end = QPointF(x2, y2)

        pen = QPen(QColor(color))
        pen.setWidth(3)
        painter.setPen(pen)

        painter.drawLine(start, end)

        # Arrow head
        head_size = 12
        angle1 = theta + math.radians(150)
        angle2 = theta - math.radians(150)

        p1 = QPointF(
            x2 + head_size * math.cos(angle1),
            y2 + head_size * math.sin(angle1)
        )

        p2 = QPointF(
            x2 + head_size * math.cos(angle2),
            y2 + head_size * math.sin(angle2)
        )

        arrow_head = QPolygonF([end, p1, p2])
        painter.setBrush(QColor(color))
        painter.drawPolygon(arrow_head)    

    def create_hsv_wheel(self, size):
        image = QImage(size, size, QImage.Format.Format_RGB32)

        cx = size / 2
        cy = size / 2
        radius = size / 2

        for y in range(size):
            for x in range(size):
                dx = x - cx
                dy = y - cy

                r = (dx * dx + dy * dy) ** 0.5

                if r <= radius:
                    hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
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
                else:
                    image.setPixelColor(x, y, QColor(255, 255, 255))

        return image

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.arrows == None:
            return

        x = (self.width() - self.image.width()) // 2
        y = (self.height() - self.image.height()) // 2

        painter.drawImage(x, y, self.image)

        for low, high, sat, color in self.arrows:
            self.draw_arrow(painter, low, sat, color)
            self.draw_arrow(painter, high, sat, color)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.hsv_wheel = HSVWheel(400)
        self.tabs.addTab(self.hsv_wheel, "HSV Color Wheel")


#app = QApplication(sys.argv)
#window = MainWindow()
#window.resize(600, 500)
#window.show()
#sys.exit(app.exec())