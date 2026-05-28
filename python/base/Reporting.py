import csv
from pathlib import Path


class Reporting:
    def __init__(self, output_dir, rpt_frames=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rpt_frames = self.normalized_report_frames(rpt_frames)
        self.written_headers = set()

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

    def particle_report_path(self, particle):
        particle_number = int(particle.pnum)
        return self.output_dir / f"p{particle_number}.csv"

    def report_particle(self, frame_number, particle):
        if not self.should_report_frame(frame_number):
            return

        csv_path = self.particle_report_path(particle)
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
                        "z",
                        "vx",
                        "vy",
                        "vz",
                        "contacts",
                        "oa",
                        "phase",
                        "target",
                        "center_distance",
                        "normal_x",
                        "normal_y",
                        "stored_mom",
                        "alpha_zero",
                        "zero_area",
                        "compression_fraction",
                        "rel_vn",
                        "closing_mom",
                    ]
                )
                self.written_headers.add(csv_path)
            writer.writerow(
                [
                    frame_number,
                    particle.pnum,
                    particle.rx,
                    particle.ry,
                    particle.rz,
                    particle.vx,
                    particle.vy,
                    particle.vz,
                    particle.report_contacts,
                    particle.oa,
                    particle.report_phase,
                    particle.report_target,
                    particle.report_center_distance,
                    particle.report_normal_x,
                    particle.report_normal_y,
                    particle.report_stored_mom,
                    particle.report_alpha_zero,
                    particle.report_zero_area,
                    particle.report_compression_fraction,
                    particle.report_rel_vn,
                    particle.report_closing_mom,
                ]
            )
        print(f"exported frame {frame_number}")

    def close(self):
        pass
