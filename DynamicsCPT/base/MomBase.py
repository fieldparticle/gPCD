import math

from base.FieldBase import FieldBase


class MomBase(FieldBase):
    """Momentum-style overlap model with inverse-square spatial attenuation.

    In this model, overlap area is treated as a momentum/velocity proxy rather
    than a force that must be time-integrated. The per-contact transfer applied
    during a substep is therefore computed directly from overlap geometry and an
    inverse-square distance law, without an extra `* sub_dt` factor.
    """

    def __init__(self):
        super().__init__()
        self.momentum_per_area = self.k
        self.inverse_square_softening = 1.0
        self.wall_inverse_square_distance = 1.0
        self.multi_contact_mode = "sum"

    def set_momentum_response(self, momentum_per_area):
        momentum_per_area = float(momentum_per_area)
        if momentum_per_area < 0.0:
            raise ValueError("momentum_per_area must be non-negative.")
        self.momentum_per_area = momentum_per_area

    def set_multi_contact_mode(self, mode):
        mode = str(mode).strip().lower()
        if mode not in {
            "sum",
            "normalize_shared",
            "sequential_descending_j",
            "sequential_ascending_j",
        }:
            raise ValueError(
                "MomBase currently supports multi_contact_mode="
                "'sum', 'normalize_shared', 'sequential_descending_j', or "
                "'sequential_ascending_j'."
            )
        self.multi_contact_mode = mode

    def inverse_square_weight(self, source_distance=None, radius_i=None, radius_j=None, delta=None):
        if source_distance is not None:
            effective_distance = abs(float(source_distance))
        elif delta is not None and radius_i is not None:
            effective_distance = max(0.0, float(radius_i) - float(delta))
        elif radius_i is not None and radius_j is not None:
            effective_distance = float(radius_i) + float(radius_j)
        elif radius_i is not None:
            effective_distance = float(radius_i)
        else:
            effective_distance = self.wall_inverse_square_distance

        softening = max(self.inverse_square_softening, 1.0e-12)
        return 1.0 / max(effective_distance * effective_distance, softening * softening)

    def field_coupling_from_overlap(
        self,
        overlap_area,
        mass_i,
        mass_j=None,
        radius_i=None,
        radius_j=None,
        source_distance=None,
        delta=None,
        force_per_area=None,
        accel_per_area=None,
    ):
        del mass_i, mass_j, force_per_area, accel_per_area
        return self.momentum_per_area * overlap_area * self.inverse_square_weight(
            source_distance=source_distance,
            radius_i=radius_i,
            radius_j=radius_j,
            delta=delta,
        )

    def field_contact_step_transfer(
        self,
        overlap_area,
        sub_dt,
        mass_i,
        mass_j=None,
        radius_i=None,
        radius_j=None,
        source_distance=None,
        delta=None,
        force_per_area=None,
        accel_per_area=None,
    ):
        del sub_dt
        return self.field_coupling_from_overlap(
            overlap_area,
            mass_i,
            mass_j,
            radius_i=radius_i,
            radius_j=radius_j,
            source_distance=source_distance,
            delta=delta,
            force_per_area=force_per_area,
            accel_per_area=accel_per_area,
        )

    def contact_force_from_area(self, area_geom, mass_i, mass_j=None):
        del mass_i, mass_j
        return self.momentum_per_area * area_geom

    def pair_contact_request_scale(self, request, pair_requests):
        if self.multi_contact_mode == "sum":
            return 1.0
        if self.multi_contact_mode == "normalize_shared":
            totals_by_particle = {}
            peak_by_particle = {}
            for other_request in pair_requests:
                magnitude = abs(other_request["equivalent_J"])
                for particle_index in (other_request["i"], other_request["j"]):
                    totals_by_particle[particle_index] = totals_by_particle.get(particle_index, 0.0) + magnitude
                    peak_by_particle[particle_index] = max(
                        peak_by_particle.get(particle_index, 0.0),
                        magnitude,
                    )

            scale = 1.0
            for particle_index in (request["i"], request["j"]):
                total = totals_by_particle.get(particle_index, 0.0)
                peak = peak_by_particle.get(particle_index, 0.0)
                if total > 1.0e-15 and peak > 0.0:
                    scale = min(scale, peak / total)
            return max(0.0, min(1.0, scale))
        if self.multi_contact_mode in {"sequential_descending_j", "sequential_ascending_j"}:
            return 1.0
        raise ValueError(f"Unsupported MomBase multi_contact_mode: {self.multi_contact_mode}")

    def ordered_pair_requests(self, pair_requests):
        if self.multi_contact_mode == "sequential_descending_j":
            return sorted(pair_requests, key=lambda request: abs(request["equivalent_J"]), reverse=True)
        if self.multi_contact_mode == "sequential_ascending_j":
            return sorted(pair_requests, key=lambda request: abs(request["equivalent_J"]))
        return pair_requests
