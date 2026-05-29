import csv
from pathlib import Path


class Reporting:
    DEFAULT_CLEAN_PATTERNS = ("*.csv",)

    def __init__(self, output_dir, rpt_frames=None, clear_existing=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if clear_existing:
            self.clear_existing_reports()
        self.rpt_frames = self.normalized_report_frames(rpt_frames)
        self.written_headers = set()
        self.written_momentum_frames = set()
        self.written_particle_frames = set()

    def clear_existing_reports(self):
        for pattern in self.DEFAULT_CLEAN_PATTERNS:
            for report_file in self.output_dir.glob(pattern):
                if report_file.is_file():
                    report_file.unlink()

    @staticmethod
    def normalized_report_frames(rpt_frames):
        if rpt_frames is None or rpt_frames is False:
            return None
        if isinstance(rpt_frames, int):
            return {rpt_frames}
        if isinstance(rpt_frames, str):
            return Reporting.normalized_report_frame_item(rpt_frames)

        frames = set()
        for frame in rpt_frames:
            frames.update(Reporting.normalized_report_frame_item(frame))
        return frames

    @staticmethod
    def normalized_report_frame_item(frame):
        if isinstance(frame, str):
            frame = frame.strip()
            if ":" in frame:
                start_frame, end_frame = frame.split(":", 1)
                start_frame = int(start_frame.strip())
                end_frame = int(end_frame.strip())
                step = 1 if start_frame <= end_frame else -1
                return set(range(start_frame, end_frame + step, step))
            return {int(frame)}
        return {int(frame)}

    def should_report_frame(self, frame_number):
        return self.rpt_frames is None or frame_number in self.rpt_frames

    def momentum_report_path(self):
        return self.output_dir / "momentum.csv"

    def particle_report_path(self, particle):
        particle_number = int(particle.pnum)
        return self.output_dir / f"p{particle_number}.csv"

    def report_frame_momentum(self, frame_number, momentum_summary):
        if not self.should_report_frame(frame_number):
            return
        if frame_number in self.written_momentum_frames:
            return

        csv_path = self.momentum_report_path()
        write_header = csv_path not in self.written_headers
        with csv_path.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            if write_header:
                writer.writerow(
                    [
                        "frame",
                        "start_total_p",
                        "start_px",
                        "start_total_py",
                        "curr_total_p",
                        "curr_px",
                        "curr_py",
                        "start_ke",
                        "curr_ke",
                        "ke_drift",
                        "start_rel_speed",
                        "curr_rel_speed",
                        "rel_speed_drift",
                    ]
                )
                self.written_headers.add(csv_path)
            writer.writerow(
                [
                    frame_number,
                    momentum_summary["start_total_p"],
                    momentum_summary["start_total_px"],
                    momentum_summary["start_total_py"],
                    momentum_summary["current_total_p"],
                    momentum_summary["current_total_px"],
                    momentum_summary["current_total_py"],
                    momentum_summary["start_ke"],
                    momentum_summary["curr_ke"],
                    momentum_summary["ke_drift"],
                    momentum_summary["start_rel_speed"],
                    momentum_summary["curr_rel_speed"],
                    momentum_summary["rel_speed_drift"],
                ]
            )
        self.written_momentum_frames.add(frame_number)

    def report_particle(self, frame_number, particle, momentum_summary=None):
        if not self.should_report_frame(frame_number):
            return

        csv_path = self.particle_report_path(particle)
        particle_frame_key = (csv_path, frame_number)
        if particle_frame_key in self.written_particle_frames:
            return

        write_header = csv_path not in self.written_headers
        with csv_path.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            if write_header:
                writer.writerow(
                    [
                        "frame",
                        "N",
                        "x",
                        "y",
                        "vx",
                        "start_total_p",
                        "start_px",
                        "start_total_py",
                        "curr_total_p",
                        "curr_px",
                        "curr_py",
                        "start_ke",
                        "curr_ke",
                        "ke_drift",
                        "start_rel_speed",
                        "curr_rel_speed",
                        "rel_speed_drift",
                        "vy",
                        "oa",
                    ]
                )
                self.written_headers.add(csv_path)
            if momentum_summary is None:
                momentum_summary = {
                    "start_total_px": 0.0,
                    "start_total_py": 0.0,
                    "start_total_p": 0.0,
                    "current_total_px": 0.0,
                    "current_total_py": 0.0,
                    "current_total_p": 0.0,
                    "start_ke": 0.0,
                    "curr_ke": 0.0,
                    "ke_drift": 0.0,
                    "start_rel_speed": 0.0,
                    "curr_rel_speed": 0.0,
                    "rel_speed_drift": 0.0,
                }
            writer.writerow(
                [
                    frame_number,
                    particle.pnum,
                    particle.rx,
                    particle.ry,
                    particle.vx,
                    momentum_summary["start_total_p"],
                    momentum_summary["start_total_px"],
                    momentum_summary["start_total_py"],
                    momentum_summary["current_total_p"],
                    momentum_summary["current_total_px"],
                    momentum_summary["current_total_py"],
                    momentum_summary["start_ke"],
                    momentum_summary["curr_ke"],
                    momentum_summary["ke_drift"],
                    momentum_summary["start_rel_speed"],
                    momentum_summary["curr_rel_speed"],
                    momentum_summary["rel_speed_drift"],
                    particle.vy,
                    particle.oa,
                ]
            )
        self.written_particle_frames.add(particle_frame_key)

    def close(self):
        pass
