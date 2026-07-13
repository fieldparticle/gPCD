import math

from gbase.GenStreaming import GenStreaming
from gbase.GenericGenData import GenericGenData


class GenLightingData(GenStreaming):
    """Generate explicit lighting/demo particles with scheduled release frames."""

    def validate_simulation_configuration(self):
        GenericGenData.validate_simulation_configuration(self)

        errors = []
        particle_data = self.itemcfg.get("PARTICLE_DATA")
        for index, configured in enumerate(self.explicit_particles):
            particle_name = f"p{index + 1}"
            particle_cfg = particle_data.get(particle_name)
            raw_release_frame = particle_cfg.get(
                "releaseFrame",
                particle_cfg.get("state_flg", 0.0),
            )
            try:
                release_frame = float(raw_release_frame)
            except (TypeError, ValueError):
                errors.append(f"PARTICLE_DATA.{particle_name}.releaseFrame must be numeric")
                continue
            if not math.isfinite(release_frame):
                errors.append(f"PARTICLE_DATA.{particle_name}.releaseFrame must be finite")
            elif release_frame < 0.0:
                errors.append(
                    f"PARTICLE_DATA.{particle_name}.releaseFrame must not be negative"
                )
            configured["release_frame"] = release_frame

        if errors:
            raise ValueError(
                "Lighting configuration error(s):\n  - "
                + "\n  - ".join(errors)
            )
        return True

    def add_explicit_mobile_particles(self):
        for configured in self.explicit_particles:
            particle = self.add_mobile_particle(
                (configured["x"], configured["y"], configured["z"]),
                (configured["vx"], configured["vy"], configured["vz"]),
                radius=configured["radius"],
                mass=configured["mass"],
                material_id=configured.get("material_id", 0),
                collision_stiffness_q=configured["collision_stiffness_q"],
            )
            particle.state_flg = float(configured.get("release_frame", 0.0))

        if self.number_active_particles != self.number_configured_particles:
            raise RuntimeError(
                "generated mobile-particle count does not match PARTICLE_DATA"
            )

        report_text = (
            "Lighting explicit-particle release report:\n"
            f"  mobile particles: {self.number_active_particles}\n"
            "  release field: PARTICLE_DATA.pN.releaseFrame -> pdata.state_flg"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return self.number_active_particles
