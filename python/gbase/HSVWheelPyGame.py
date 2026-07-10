import math
import colorsys
import pygame


class HSVWheel:
    """Pygame HSV wheel with velocity-angle arrows.

    Particle arrows are passed with set_particle_angles().  Each arrow is drawn
    using standard Cartesian angle convention:

        0 degrees   -> right
        90 degrees  -> up
        180 degrees -> left
        270 degrees -> down
    """

    def __init__(self, size=400):
        self.size = int(size)
        self.image = self.create_hsv_wheel(self.size)

        # Optional manual reference arrow controlled by A/D.
        self.angle_deg = 0.0
        self.show_reference_arrow = False

        # Entries are dictionaries with keys: pnum, angle_deg, saturation, color.
        self.particle_angles = []

    def set_particle_angles(self, particle_angles):
        """Set particle velocity arrows.

        Accepted input formats:
            [(particle_number, angle_degrees), ...]
            [(particle_number, angle_degrees, saturation), ...]
            [(particle_number, angle_degrees, saturation, color), ...]
            [{"pnum": n, "angle_deg": a}, ...]
        """
        normalized = []

        for item in particle_angles or []:
            if isinstance(item, dict):
                pnum = int(item.get("pnum", item.get("particle_number", 0)))
                angle_deg = float(item.get("angle_deg", item.get("angle", 0.0)))
                saturation = float(item.get("saturation", 0.92))
                color = item.get("color", (0, 0, 0))
            else:
                if len(item) < 2:
                    continue
                pnum = int(item[0])
                angle_deg = float(item[1])
                saturation = float(item[2]) if len(item) >= 3 else 0.92
                color = item[3] if len(item) >= 4 else (0, 0, 0)

            normalized.append(
                {
                    "pnum": pnum,
                    "angle_deg": angle_deg % 360.0,
                    "saturation": max(0.0, min(1.0, saturation)),
                    "color": color,
                }
            )

        self.particle_angles = normalized

    def create_hsv_wheel(self, size):
        surface = pygame.Surface((size, size))
        cx = size / 2.0
        cy = size / 2.0
        radius = size / 2.0

        for y in range(size):
            for x in range(size):
                dx = x - cx
                dy = y - cy
                r = math.sqrt(dx * dx + dy * dy)

                if r <= radius:
                    # Screen y is downward, so use -dy to make the wheel use
                    # standard Cartesian angle orientation.
                    hue = (math.atan2(-dy, dx) / (2.0 * math.pi)) % 1.0
                    sat = r / radius
                    val = 1.0
                    red, green, blue = colorsys.hsv_to_rgb(hue, sat, val)
                    surface.set_at(
                        (x, y),
                        (int(red * 255), int(green * 255), int(blue * 255)),
                    )
                else:
                    surface.set_at((x, y), (255, 255, 255))

        return surface.convert()

    def _arrow_tip(self, origin, angle_deg, saturation):
        cx, cy = origin
        radius = self.size / 2.0
        length = max(0.0, min(1.0, saturation)) * radius
        theta = math.radians(angle_deg)

        x2 = cx + length * math.cos(theta)
        y2 = cy - length * math.sin(theta)
        return x2, y2, theta

    def draw_arrow(self, screen, center, angle_deg, saturation=0.92, color=(0, 0, 0)):
        x2, y2, theta = self._arrow_tip(center, angle_deg, saturation)
        end = (x2, y2)

        pygame.draw.line(screen, color, center, end, 2)

        head_size = max(7, int(self.size * 0.030))
        angle1 = theta + math.radians(150)
        angle2 = theta - math.radians(150)

        p1 = (
            x2 + head_size * math.cos(angle1),
            y2 - head_size * math.sin(angle1),
        )
        p2 = (
            x2 + head_size * math.cos(angle2),
            y2 - head_size * math.sin(angle2),
        )

        pygame.draw.polygon(screen, color, [end, p1, p2])
        return end

    def draw_text(self, screen, font, pos):
        rad = math.radians(self.angle_deg)
        text = f"DEG: {self.angle_deg:6.1f}   RAD: {rad:7.4f}"
        img = font.render(text, True, (0, 0, 0))
        screen.blit(img, pos)

    def draw_particle_labels(self, screen, center, font):
        label_font = font
        for entry in self.particle_angles:
            tip = self.draw_arrow(
                screen,
                center,
                entry["angle_deg"],
                entry["saturation"],
                entry["color"],
            )

            label = label_font.render(str(entry["pnum"]), True, entry["color"])
            label_rect = label.get_rect()
            label_rect.centerx = int(tip[0])
            label_rect.top = int(tip[1]) + 4
            screen.blit(label, label_rect)

    def draw(self, screen, pos, font):
        x, y = pos
        screen.blit(self.image, (x, y))

        center = (x + self.size / 2.0, y + self.size / 2.0)

        self.draw_particle_labels(screen, center, font)

        if self.show_reference_arrow:
            self.draw_arrow(screen, center, self.angle_deg, 1.0, (255, 255, 255))

        self.draw_text(screen, font, (x, y + self.size + 6))
