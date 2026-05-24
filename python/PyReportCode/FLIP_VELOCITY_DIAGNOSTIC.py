import math
import re
import csv
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None


class FLIP_VELOCITY_DIAGNOSTIC:
    """Plot contact-state diagnostics from gPCD frame capture reports.

    The default settings target the TwoParticleChaseWall case:
    source particle P1, partner particle P0, and the right wall.
    """

    FLOAT_PATTERN = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"

    def __init__(
        self,
        reports_dir=r"C:\_DJ\gPCDData\examples\reports",
        output_file=None,
        source_particle=1,
        partner_particle=0,
        wall_name="right",
        wall_xmax=4.0,
        particle_radius=0.25,
    ):
        self.reports_dir = Path(reports_dir)
        self.output_file = (
            Path(output_file)
            if output_file is not None
            else self.reports_dir / "FLIP_VELOCITY_DIAGNOSTIC.png"
        )
        self.csv_file = self.output_file.with_suffix(".csv")
        self.source_particle = source_particle
        self.partner_particle = partner_particle
        self.wall_name = wall_name
        self.wall_xmax = wall_xmax
        self.particle_radius = particle_radius

    def run(self):
        rows = self.load_reports()
        if not rows:
            raise RuntimeError(f"No capture rows found in {self.reports_dir}")
        self.write_csv(rows)
        if plt is None:
            raise RuntimeError(
                "matplotlib is not available in this Python environment. "
                f"Wrote parsed diagnostic CSV instead: {self.csv_file}"
            )
        self.plot(rows)
        return self.output_file

    def load_reports(self):
        rows = []
        for report_file in sorted(self.reports_dir.glob("Cap*.rpt")):
            row = self.parse_report(report_file)
            if row is not None:
                rows.append(row)
        return rows

    def parse_report(self, report_file):
        lines = report_file.read_text(encoding="utf-8").splitlines()
        row = {
            "file": str(report_file),
            "frame": self.frame_from_name(report_file),
            "boundary_error": 0.0,
            "has_guardrail": 0.0,
        }

        section = None
        current_particle = None
        current_contact = None
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("[") and line.endswith("]"):
                section = line
                current_particle = self.parse_particle_header(line)
                current_contact = self.parse_contact_header(line)
                if line == "[guardrail_errors]":
                    row["has_guardrail"] = 1.0
                continue

            if section == "[summary]":
                match = re.search(r"frame=(\d+)", line)
                if match:
                    row["frame"] = int(match.group(1))
                continue

            if section == "[guardrail_errors]":
                self.parse_guardrail_line(row, line)
                continue

            if current_particle is not None:
                self.parse_particle_line(row, current_particle, line)
                continue

            if current_contact is not None:
                self.parse_contact_line(row, current_contact, line)
                continue

        self.add_derived_values(row)
        return row

    @staticmethod
    def frame_from_name(report_file):
        match = re.search(r"Cap(\d+)\.rpt$", report_file.name)
        return int(match.group(1)) if match else -1

    @staticmethod
    def parse_particle_header(line):
        match = re.match(r"\[particle p(\d+) Neo \]", line)
        return int(match.group(1)) if match else None

    @staticmethod
    def parse_contact_header(line):
        pair_match = re.match(r"\[particle P(\d+) Collision\]", line)
        if pair_match:
            return {"kind": "pair", "source": int(pair_match.group(1))}

        wall_match = re.match(r"\[particle P(\d+) WallCollision\]", line)
        if wall_match:
            return {"kind": "wall", "source": int(wall_match.group(1))}

        return None

    def parse_guardrail_line(self, row, line):
        source = self.source_particle
        match = re.search(
            rf"ERROR p{source} boundary_exceeded .*x=({self.FLOAT_PATTERN})>xmax=({self.FLOAT_PATTERN})",
            line,
        )
        if match:
            x_value = float(match.group(1))
            xmax = float(match.group(2))
            row["boundary_error"] = max(row.get("boundary_error", 0.0), x_value - xmax)
            row["wall_xmax"] = xmax

    def parse_particle_line(self, row, particle_index, line):
        prefix = f"p{particle_index}"
        if line.startswith("loc:"):
            values = self.float_values(line)
            if len(values) >= 2:
                row[f"{prefix}_x"] = values[0]
                row[f"{prefix}_y"] = values[1]
        elif line.startswith("v:"):
            values = self.float_values(line)
            if len(values) >= 2:
                row[f"{prefix}_vx"] = values[0]
                row[f"{prefix}_vy"] = values[1]
        elif line.startswith("px:"):
            row[f"{prefix}_px"] = self.first_float(line)
        elif line.startswith("py:"):
            row[f"{prefix}_py"] = self.first_float(line)

    def parse_contact_line(self, row, contact, line):
        if contact["source"] != self.source_particle:
            return

        if contact["kind"] == "pair":
            self.parse_pair_contact_line(row, line)
        elif contact["kind"] == "wall":
            self.parse_wall_contact_line(row, line)

    def parse_pair_contact_line(self, row, line):
        if line.startswith("c"):
            match = re.match(r"c(\d+)->(\d+)", line)
            if match and int(match.group(2)) != self.partner_particle:
                row["_skip_pair_contact"] = True
            else:
                row["_skip_pair_contact"] = False
            return
        if row.get("_skip_pair_contact", False):
            return

        self.parse_prefixed_metric(row, "pair", line)

    def parse_wall_contact_line(self, row, line):
        if line.startswith("wall="):
            row["_skip_wall_contact"] = line.split("=", 1)[1] != self.wall_name
            return
        if row.get("_skip_wall_contact", False):
            return

        self.parse_prefixed_metric(row, "wall", line)

    def parse_prefixed_metric(self, row, prefix, line):
        if "=" not in line:
            return
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key in {"phase", "imode", "mode", "zsrc", "lock"}:
            row[f"{prefix}_{key}"] = value
            return

        number = self.first_float(value)
        if number is not None:
            row[f"{prefix}_{key}"] = number

    def add_derived_values(self, row):
        source = self.source_particle
        partner = self.partner_particle
        source_x = row.get(f"p{source}_x")
        partner_x = row.get(f"p{partner}_x")
        source_vx = row.get(f"p{source}_vx")
        partner_vx = row.get(f"p{partner}_vx")
        radius = self.particle_radius
        wall_xmax = row.get("wall_xmax", self.wall_xmax)

        if source_x is not None:
            row["wall_distance_to_xmax"] = wall_xmax - source_x
            row["source_boundary_error"] = max(0.0, source_x - wall_xmax)
        if source_x is not None and partner_x is not None:
            pair_distance = abs(source_x - partner_x)
            row["pair_center_distance_from_position"] = pair_distance
            row["pair_overlap_depth_from_position"] = max(0.0, 2.0 * radius - pair_distance)
        if source_vx is not None and partner_vx is not None:
            row["relative_vx_partner_minus_source"] = partner_vx - source_vx
        if row.get("wall_center_distance") is not None:
            row["wall_overlap_depth"] = max(0.0, 2.0 * radius - row["wall_center_distance"])

    @classmethod
    def float_values(cls, text):
        return [float(value) for value in re.findall(cls.FLOAT_PATTERN, text)]

    @classmethod
    def first_float(cls, text):
        values = cls.float_values(text)
        return values[0] if values else None

    @staticmethod
    def series(rows, key, default=math.nan):
        return [row.get(key, default) for row in rows]

    def write_csv(self, rows):
        keys = sorted({key for row in rows for key in row if not key.startswith("_")})
        self.csv_file.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_file.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=keys)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in keys})

    @staticmethod
    def state_series(rows, key):
        labels = []
        values = []
        label_index = {}
        for row in rows:
            label = row.get(key, "")
            if label not in label_index:
                label_index[label] = len(label_index)
                labels.append(label)
            values.append(label_index[label])
        return values, labels

    def plot(self, rows):
        frames = self.series(rows, "frame")
        fig, axes = plt.subplots(5, 1, figsize=(13, 14), sharex=True)
        fig.suptitle(
            f"Flip Velocity Diagnostic: P{self.source_particle}, "
            f"P{self.partner_particle}, {self.wall_name} wall"
        )

        self.plot_positions(axes[0], frames, rows)
        self.plot_penetration(axes[1], frames, rows)
        self.plot_velocity(axes[2], frames, rows)
        self.plot_state(axes[3], frames, rows)
        self.plot_momentum(axes[4], frames, rows)

        axes[-1].set_xlabel("frame")
        for axis in axes:
            axis.grid(True, alpha=0.28)
            self.mark_guardrails(axis, rows)
            axis.legend(loc="best", fontsize=8)

        fig.tight_layout(rect=(0, 0, 1, 0.97))
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(self.output_file, dpi=150)
        plt.close(fig)

    def plot_positions(self, axis, frames, rows):
        source = self.source_particle
        partner = self.partner_particle
        axis.plot(frames, self.series(rows, f"p{source}_x"), label=f"P{source}.x")
        axis.plot(frames, self.series(rows, f"p{partner}_x"), label=f"P{partner}.x")
        axis.axhline(self.wall_xmax, color="black", linestyle="--", linewidth=1.0, label="xmax")
        axis.plot(
            frames,
            self.series(rows, "source_boundary_error"),
            label="boundary error",
            color="red",
            linestyle=":",
        )
        axis.set_ylabel("position")

    def plot_penetration(self, axis, frames, rows):
        axis.plot(
            frames,
            self.series(rows, "wall_overlap_depth"),
            label="wall overlap depth",
        )
        axis.plot(
            frames,
            self.series(rows, "pair_overlap_depth_from_position"),
            label="pair overlap depth",
        )
        axis.axhline(
            self.particle_radius,
            color="red",
            linestyle="--",
            linewidth=1.0,
            label="50% overlap limit",
        )
        axis.set_ylabel("penetration")

    def plot_velocity(self, axis, frames, rows):
        source = self.source_particle
        partner = self.partner_particle
        axis.plot(frames, self.series(rows, f"p{source}_vx"), label=f"P{source}.vx")
        axis.plot(frames, self.series(rows, f"p{partner}_vx"), label=f"P{partner}.vx")
        axis.plot(frames, self.series(rows, "wall_vn"), label="wall vn")
        axis.plot(frames, self.series(rows, "pair_reln"), label="pair reln")
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_ylabel("velocity")

    def plot_state(self, axis, frames, rows):
        wall_imode, wall_imode_labels = self.state_series(rows, "wall_imode")
        wall_lock, wall_lock_labels = self.state_series(rows, "wall_lock")
        wall_phase, wall_phase_labels = self.state_series(rows, "wall_phase")
        pair_imode, pair_imode_labels = self.state_series(rows, "pair_imode")

        axis.step(frames, wall_imode, where="post", label="wall imode")
        axis.step(frames, [value + 0.12 for value in wall_lock], where="post", label="wall lock")
        axis.step(frames, [value + 0.24 for value in wall_phase], where="post", label="wall phase")
        axis.step(frames, [value + 0.36 for value in pair_imode], where="post", label="pair imode")
        axis.set_ylabel("state")
        notes = [
            "wall imode: " + ", ".join(f"{i}={label}" for i, label in enumerate(wall_imode_labels)),
            "wall lock: " + ", ".join(f"{i}={label}" for i, label in enumerate(wall_lock_labels)),
            "wall phase: " + ", ".join(f"{i}= {label}" for i, label in enumerate(wall_phase_labels)),
            "pair imode: " + ", ".join(f"{i}= {label}" for i, label in enumerate(pair_imode_labels)),
        ]
        axis.text(
            0.01,
            0.03,
            "\n".join(notes),
            transform=axis.transAxes,
            fontsize=8,
            va="bottom",
            bbox={"facecolor": "white", "alpha": 0.72, "edgecolor": "none"},
        )

    def plot_momentum(self, axis, frames, rows):
        axis.plot(frames, self.series(rows, "wall_istore"), label="wall istore")
        axis.plot(frames, self.series(rows, "wall_irel"), label="wall irel")
        axis.plot(frames, self.series(rows, "wall_irem"), label="wall irem")
        axis.plot(frames, self.series(rows, "wall_return_vn"), label="wall return vn")
        axis.plot(frames, self.series(rows, "wall_block_vn"), label="wall blocked vn")
        axis.plot(frames, self.series(rows, "pair_istore"), label="pair istore")
        axis.plot(frames, self.series(rows, "pair_irel"), label="pair irel")
        axis.plot(frames, self.series(rows, "pair_irem"), label="pair irem")
        axis.plot(frames, self.series(rows, "pair_return_reln"), label="pair return reln")
        axis.plot(frames, self.series(rows, "pair_block_reln"), label="pair blocked reln")
        axis.set_ylabel("momentum")

    @staticmethod
    def mark_guardrails(axis, rows):
        for row in rows:
            if row.get("has_guardrail", 0.0):
                axis.axvline(row["frame"], color="red", alpha=0.12, linewidth=1.0)


if __name__ == "__main__":
    output = FLIP_VELOCITY_DIAGNOSTIC().run()
    print(f"Wrote {output}")
