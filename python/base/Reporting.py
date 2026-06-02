import csv
from pathlib import Path


class Reporting:
    CAPTURE_FILE_SUFFIX = ".csv"

    def __init__(self, output_dir, rpt_frames=None, clear_existing=True, file_suffix=""):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.file_suffix = file_suffix
        self.cleared_report_count = 0
        if clear_existing:
            self.cleared_report_count = self.clear_existing_reports()
        self.rpt_frames = self.normalized_report_frames(rpt_frames)
        self.written_headers = set()
        self.written_momentum_frames = set()
        self.written_particle_frames = set()
        self.written_contact_frames = set()

    def clear_existing_reports(self):
        deleted_count = 0
        for report_file in self.output_dir.iterdir():
            if (
                report_file.is_file()
                and report_file.suffix.lower() == self.CAPTURE_FILE_SUFFIX
            ):
                report_file.unlink()
                deleted_count += 1
        return deleted_count

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
        return self.output_dir / f"momentum{self.file_suffix}.csv"

    def particle_report_path(self, particle):
        particle_number = int(particle.pnum)
        return self.output_dir / f"p{particle_number}{self.file_suffix}.csv"

    def contacts_report_path(self):
        return self.output_dir / f"contacts{self.file_suffix}.csv"

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
                        "total_internal_mom",
                        "curr_plus_internal_mom",
                        "start_minus_curr_plus_internal_mom",
                        "start_ke",
                        "curr_ke",
                        "frame_start_ke",
                        "after_resolve_ke",
                        "ke_drift",
                        "v_rel",
                        "raw_impulse",
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
                    momentum_summary["total_internal_mom"],
                    momentum_summary["curr_plus_internal_mom"],
                    momentum_summary["start_minus_curr_plus_internal_mom"],
                    momentum_summary["start_ke"],
                    momentum_summary["curr_ke"],
                    momentum_summary["frame_start_ke"],
                    momentum_summary["after_resolve_ke"],
                    momentum_summary["ke_drift"],
                    momentum_summary["v_rel"],
                    momentum_summary["raw_impulse"],
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
                        "vy",
                        "internal_mom",
                        "particle_frame_start_ke",
                        "particle_after_resolve_ke",
                    ]
                )
                self.written_headers.add(csv_path)
            writer.writerow(
                [
                    frame_number,
                    particle.pnum,
                    particle.rx,
                    particle.ry,
                    particle.vx,
                    particle.vy,
                    getattr(particle, "report_stored_mom", 0.0),
                    getattr(particle, "report_frame_start_ke", 0.0),
                    getattr(particle, "report_after_resolve_ke", 0.0),
                ]
            )
        self.written_particle_frames.add(particle_frame_key)

    def report_contacts(self, frame_number, particles):
        if not self.should_report_frame(frame_number):
            return
        if frame_number in self.written_contact_frames:
            return

        csv_path = self.contacts_report_path()
        write_header = csv_path not in self.written_headers
        contact_diagnostic_columns = [
            "raw_impulse",
            "compression_impulse",
            "release_impulse",
            "source_available_momentum",
            "source_available_share",
            "target_available_momentum",
            "target_available_share",
            "weighted_available_momentum",
            "source_vn",
            "target_vn",
            "rel_vn",
            "delta_px",
            "delta_py",
            "delta_pz",
            "source_vx_before",
            "source_vy_before",
            "source_vz_before",
            "source_vx_after",
            "source_vy_after",
            "source_vz_after",
            "source_ke_before",
            "source_ke_after",
            "source_ke_delta",
            "contact_ke_delta_estimate",
            "source_net_delta_px",
            "source_net_delta_py",
            "source_net_delta_pz",
            "source_net_ke_delta_estimate",
            "source_contact_ke_delta_sum",
            "source_ke_cross_term",
            "source_ke_residual",
        ]
        with csv_path.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            if write_header:
                writer.writerow(
                    [
                        "frame",
                        "source_index",
                        "source",
                        "target_index",
                        "target",
                        "slot",
                        "source_contact_count",
                        "source_targets",
                        "source_total_overlap_area",
                        "target_total_overlap_area",
                        "overlap_area",
                        "source_area_weight",
                        "target_area_weight",
                        "phase",
                        "stored_mom",
                        "applied_impulse",
                        *contact_diagnostic_columns,
                        "normal_x",
                        "normal_y",
                        "normal_z",
                        "center_distance",
                        "penetration_depth",
                    ]
                )
                self.written_headers.add(csv_path)

            active_by_source = self.active_contacts_by_source(particles)
            total_overlap_by_source = {
                source_index: sum(max(0.0, contact.geom.w) for _slot, contact in contacts)
                for source_index, contacts in active_by_source.items()
            }

            for source_index, particle in enumerate(particles):
                contacts = active_by_source.get(source_index, [])
                source_targets = "|".join(
                    str(self.particle_number_for_index(particles, contact.ids.x))
                    for _slot, contact in contacts
                )
                if not contacts:
                    writer.writerow(
                        [
                            frame_number,
                            source_index,
                            particle.pnum,
                            "",
                            "",
                            "",
                            0,
                            "",
                            0.0,
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            *["" for _column in contact_diagnostic_columns],
                            "",
                            "",
                            "",
                            "",
                            "",
                        ]
                    )
                    continue

                source_total_overlap_area = total_overlap_by_source.get(source_index, 0.0)
                for slot, contact in contacts:
                    target_index = int(contact.ids.x)
                    target_total_overlap_area = total_overlap_by_source.get(target_index, 0.0)
                    overlap_area = max(0.0, contact.geom.w)
                    source_area_weight = (
                        overlap_area / source_total_overlap_area
                        if source_total_overlap_area > 1.0e-12
                        else 0.0
                    )
                    target_area_weight = (
                        overlap_area / target_total_overlap_area
                        if target_total_overlap_area > 1.0e-12
                        else 0.0
                    )
                    writer.writerow(
                        [
                            frame_number,
                            source_index,
                            particle.pnum,
                            target_index,
                            self.particle_number_for_index(particles, target_index),
                            slot,
                            len(contacts),
                            source_targets,
                            source_total_overlap_area,
                            target_total_overlap_area,
                            overlap_area,
                            source_area_weight,
                            target_area_weight,
                            contact.ids.z,
                            contact.aux.z,
                            contact.aux.w,
                            getattr(contact, "raw_impulse", 0.0),
                            getattr(contact, "compression_impulse", 0.0),
                            getattr(contact, "release_impulse", 0.0),
                            getattr(contact, "source_available_momentum", 0.0),
                            getattr(contact, "source_available_share", 0.0),
                            getattr(contact, "target_available_momentum", 0.0),
                            getattr(contact, "target_available_share", 0.0),
                            getattr(contact, "weighted_available_momentum", 0.0),
                            getattr(contact, "source_vn", 0.0),
                            getattr(contact, "target_vn", 0.0),
                            getattr(contact, "rel_vn", 0.0),
                            getattr(contact, "delta_px", 0.0),
                            getattr(contact, "delta_py", 0.0),
                            getattr(contact, "delta_pz", 0.0),
                            getattr(contact, "source_vx_before", 0.0),
                            getattr(contact, "source_vy_before", 0.0),
                            getattr(contact, "source_vz_before", 0.0),
                            getattr(contact, "source_vx_after", 0.0),
                            getattr(contact, "source_vy_after", 0.0),
                            getattr(contact, "source_vz_after", 0.0),
                            getattr(contact, "source_ke_before", 0.0),
                            getattr(contact, "source_ke_after", 0.0),
                            getattr(contact, "source_ke_delta", 0.0),
                            getattr(contact, "contact_ke_delta_estimate", 0.0),
                            getattr(contact, "source_net_delta_px", 0.0),
                            getattr(contact, "source_net_delta_py", 0.0),
                            getattr(contact, "source_net_delta_pz", 0.0),
                            getattr(contact, "source_net_ke_delta_estimate", 0.0),
                            getattr(contact, "source_contact_ke_delta_sum", 0.0),
                            getattr(contact, "source_ke_cross_term", 0.0),
                            getattr(contact, "source_ke_residual", 0.0),
                            contact.geom.x,
                            contact.geom.y,
                            contact.geom.z,
                            contact.aux.x,
                            contact.aux.y,
                        ]
                    )

        self.written_contact_frames.add(frame_number)

    @staticmethod
    def active_contacts_by_source(particles):
        active_by_source = {}
        for source_index, particle in enumerate(particles):
            contacts = getattr(particle, "contacts", getattr(particle, "gcs", []))
            active_contacts = []
            for slot, contact in enumerate(contacts):
                if getattr(contact.ids, "w", 0) == 1 and getattr(contact.ids, "y", 0) == 1:
                    active_contacts.append((slot, contact))
            active_by_source[source_index] = active_contacts
        return active_by_source

    @staticmethod
    def particle_number_for_index(particles, particle_index):
        if 0 <= int(particle_index) < len(particles):
            return particles[int(particle_index)].pnum
        return ""

    def close(self):
        pass
