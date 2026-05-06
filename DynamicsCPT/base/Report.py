class Report:
    """Per-particle in-memory report storage."""

    def __init__(self):
        self.particles = {}

    def clear(self):
        self.particles = {}

    def ensure_particle(self, particle_index):
        if particle_index not in self.particles:
            self.particles[particle_index] = []
        return self.particles[particle_index]

    def record_particle(self, particle_index, row):
        self.ensure_particle(particle_index).append(dict(row))

    def particle_rows(self, particle_index):
        return self.particles.get(particle_index, [])

    def latest_particle(self, particle_index):
        rows = self.particle_rows(particle_index)
        if not rows:
            return None
        return rows[-1]
