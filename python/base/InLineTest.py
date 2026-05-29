import csv
import argparse
from pathlib import Path


class InLineTest:
    
    def __init__(self, *args, **kwargs):
        self.item_cfg = {}
        self.max_penetration_particle_number = 1
        self.max_penetration_depth = 0.0
        self.max_penetration_path = None
        self.study_velocity_initialized = False
    
    def BeforeContactScan(self, particles):
        if self.study_velocity_initialized:
            return
        self.particles = particles
        self.vx = 0.05
        if self.study_number == 0:
            self.vx = 0.05
        elif self.study_number == 1:
            self.vx = 0.045
        elif self.study_number == 2:
            self.vx = 0.04
        elif self.study_number == 3:
            self.vx = 0.035
        elif self.study_number == 4: 
            self.vx = 0.03
        elif self.study_number == 5:
            self.vx = 0.025
        elif self.study_number == 6:
            self.vx = 0.02
        elif self.study_number == 7:
            self.vx = 0.015
        elif self.study_number == 8:
            self.vx = 0.01
        for particle in self.particles:
            if particle.pnum == 1:
                particle.VelRad.x = self.vx
            if particle.pnum == 2:
                particle.VelRad.x = -self.vx
        self.study_velocity_initialized = True


    def Create(self,config_obj, study_number):
        self.study_number = study_number
        self.item_cfg = config_obj
        self.max_penetration_particle_number = 1
        self.max_penetration_depth = 0.0
        self.study_velocity_initialized = False
        run_configuration = self.RunConfiguration()
        output_dir = self.OutputDir(run_configuration)
        output_dir.mkdir(parents=True, exist_ok=True)
        study_number = 0 if self.study_number is None else int(self.study_number)
        self.max_penetration_path = output_dir / f"inline_max_penetration{study_number:04d}.csv"
        with self.max_penetration_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "study",
                    "particle",
                    "frame",
                    "max_penetration_depth",
                    "vx",
                    "vy",
                    "vz",
                    "dt",
                    "collision_stiffness_q",
                ]
            )
        # Open the item configuration file+

    def DecrementStiffness(self, particles):
        new_stiffness = None
        for particle in particles:
            particle.Data.y = max(0.0, particle.Data.y - 0.1)
            new_stiffness = particle.Data.y
        return 0.0 if new_stiffness is None else new_stiffness

    def RunConfiguration(self):
        if "RUN_CONFIGURATION" in self.item_cfg:
            return self.item_cfg.get("RUN_CONFIGURATION", {})
        return self.item_cfg

    def OutputDir(self, run_configuration):
        if "run_debug_dir" in run_configuration:
            return Path(run_configuration["run_debug_dir"])
        if "RUN_CONFIGURATION" in self.item_cfg:
            data_dir = Path(self.item_cfg.get("data_dir", "C:/_DJ/gPCDData/examples"))
            study_name = self.item_cfg.get("STUDY_NAME", "inline_test")
            return data_dir / "rpt" / study_name
        return Path("C:/_DJ/gPCDData/examples/rpt/inline_test")

    def StartRun(self, particles):
        self.particles = particles
        for particle in self.particles:
            # Example modification: reverse the x-velocity of particles with rx < 1.8 or rx > 2.35
            particle_x = self.ActiveX(particle)
            if particle.pnum == 1 and particle_x < 1.5:
                collision_stiffness_q = self.DecrementStiffness(self.particles)
                print(f"collision_stiffness_q={collision_stiffness_q}")
                particle.VelRad.x = particle.VelRad.x * -1.0
                particle.PosLocA.x = 1.5
                particle.PosLocB.x = 1.5
            if particle.pnum == 2 and particle_x > 2.65:
                particle.VelRad.x = particle.VelRad.x * -1.0
                particle.PosLocA.x = 2.65
                particle.PosLocB.x = 2.65
        return self.particles

    def ActiveX(self, particle):
        if particle.PosLocA.w == 0.0:
            return particle.PosLocA.x
        return particle.PosLocB.x

    def AfterContactScan(self, frame_number, particle, dt, collision_stiffness_q):
        if self.max_penetration_path is None:
            return
        if particle.pnum != self.max_penetration_particle_number:
            return
        if particle.max_penetration_depth <= self.max_penetration_depth:
            return
        self.max_penetration_depth = particle.max_penetration_depth
        with self.max_penetration_path.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    self.study_number,
                    particle.pnum,
                    frame_number,
                    particle.max_penetration_depth,
                    particle.VelRad.x,
                    particle.VelRad.y,
                    particle.VelRad.z,
                    dt,
                    collision_stiffness_q,
                ]
            )


def read_max_depth_by_stiffness(csv_path):
    max_depth_by_stiffness = {}
    with Path(csv_path).open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if not row:
                continue
            stiffness = float(row["collision_stiffness_q"])
            depth = float(row["max_penetration_depth"])
            max_depth_by_stiffness[stiffness] = max(
                max_depth_by_stiffness.get(stiffness, 0.0),
                depth,
            )
    return max_depth_by_stiffness


def plot_max_depth_by_stiffness(csv_path, output_path=None):
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "matplotlib is required for standalone plotting. "
            "Install it in this Python environment or run from an environment "
            "that already has matplotlib."
        ) from exc

    max_depth_by_stiffness = read_max_depth_by_stiffness(csv_path)
    if not max_depth_by_stiffness:
        raise ValueError(f"No rows found in {csv_path}")

    stiffness_values = sorted(max_depth_by_stiffness)
    max_depth_values = [
        max_depth_by_stiffness[stiffness]
        for stiffness in stiffness_values
    ]

    fig, ax = plt.subplots()
    ax.plot(stiffness_values, max_depth_values, marker="o")
    ax.set_xlabel("collision_stiffness_q")
    ax.set_ylabel("max penetration depth")
    ax.set_title("Max Penetration Depth vs Stiffness")
    ax.grid(True)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path)
        print(f"saved plot {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Plot max penetration depth versus collision stiffness.",
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="C:/_DJ/gPCDData/examples/rpt/TwoParticleHorizontal/inline_max_penetration.csv",
        help="Path to inline_max_penetration.csv",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Optional output image path. If omitted, show the plot window.",
    )
    args = parser.parse_args()
    plot_max_depth_by_stiffness(args.csv_path, args.output)


if __name__ == "__main__":
    main()
