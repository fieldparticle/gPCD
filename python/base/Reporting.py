import csv
from pathlib import Path


class Reporting:
    def __init__(self, output_dir, rpt_frames=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rpt_frames = self.normalized_report_frames(rpt_frames)

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

    def particle_report_path(self, frame_number, particle):
        particle_number = int(particle.pnum)
        return self.output_dir / f"p{particle_number}{frame_number:06d}.csv"

    def report_particle(self, frame_number, particle):
        if not self.should_report_frame(frame_number):
            return

        csv_path = self.particle_report_path(frame_number, particle)
        with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["N", "x", "y", "z", "vx", "vy", "vz"])
            writer.writerow(
                [
                    particle.pnum,
                    particle.rx,
                    particle.ry,
                    particle.rz,
                    particle.vx,
                    particle.vy,
                    particle.vz,
                ]
            )
        print(f"exported frame {frame_number}")

    def close(self):
        pass
