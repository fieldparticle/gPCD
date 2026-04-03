from base.FieldBase import FieldBase

DEFAULT_WALL_BOX = (-4.0, 4.0, -5.0, 6.0)


def configure_default_walls(base):
    base.set_walls(*DEFAULT_WALL_BOX)


def configure_three_particle_horizontal(base):
    base.clear_particles()
    base.clear_walls()
    base.set_scenario_options(post_collision_frames=90)
    base.add_particle(x=-2.0, y=1.5, vx=1.0, vy=0.0, mass=1.0, radius=1.0)
    base.add_particle(x=2.0, y=0.0, vx=-1.0, vy=0.0, mass=1.0, radius=1.0)
    base.add_particle(x=2.0, y=3.0, vx=-1.0, vy=0.0, mass=1.0, radius=1.0)


def configure_three_particle_horizontal_in_box(base):
    configure_three_particle_horizontal(base)
    configure_default_walls(base)


def configure_two_particle_horizontal(base):
    base.clear_particles()
    base.clear_walls()
    base.set_scenario_options(post_collision_frames=90)
    base.add_particle(x=-2.0, y=0.0, vx=1.0, vy=0.0, mass=1.0, radius=1.0)
    base.add_particle(x=2.0, y=0.0, vx=-1.0, vy=0.0, mass=1.0, radius=1.0)


def configure_two_particle_horizontal_in_box(base):
    configure_two_particle_horizontal(base)
    configure_default_walls(base)
    base.set_scenario_options(post_collision_frames=None)


def configure_two_particle_angled(base):
    base.clear_particles()
    base.clear_walls()
    base.set_scenario_options(post_collision_frames=90)
    base.add_particle(x=-2.15, y=2.0, vx=0.5, vy=-0.5, mass=1.0, radius=1.0)
    base.add_particle(x=-1.0, y=-1.0, vx=-0.5, vy=0.5, mass=1.0, radius=1.0)

def configure_two_particle_ocl(base):
    base.clear_particles()
    base.clear_walls()
    base.set_scenario_options(post_collision_frames=90)
    base.add_particle(x=-2.0, y=1.5, vx=1.0, vy=0.0, mass=1.0, radius=1.0)
    base.add_particle(x=2.0, y=0.0, vx=-1.0, vy=0.0, mass=1.0, radius=1.0)

def configure_two_particle_angled_in_box(base):
    configure_two_particle_angled(base)
    configure_default_walls(base)


def configure_two_particle_horizontal_no_post_stop(base):
    configure_two_particle_horizontal(base)
    base.set_scenario_options(post_collision_frames=None)


def configure_two_particle_horizontal_bonded(base):
    configure_two_particle_horizontal(base)
    base.set_scenario_options(post_collision_frames=None)
    base.k = 1.9
    base.set_bonding(
        stiffness=8.0,
        damping=0.15,
        rest_length_offset=-1.0,
        max_distance=4.0,
        activation_distance=1.0,
    )


def build_base(configure_scenario):
    base = FieldBase()
    configure_scenario(base)
    base.reset()
    return base
