class GeoDynamics:
    def GeoAddParticleContact(self, SourceID, TargetID):
        particle = self.particles[SourceID]
        if TargetID not in particle.collision_list:
            particle.collision_list.append(TargetID)

    def GeoMoveParticle(self, SourceID, positionBuffer, dt):
        particle = self.particles[SourceID]
        particle.rx += particle.vx * dt
        particle.ry += particle.vy * dt
        particle.rz += particle.vz * dt

    def GeoProcessCollisions(self, SourceID):
        pass
