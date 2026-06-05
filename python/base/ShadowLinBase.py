from base.ShadowBase import ShadowBase
from base.ShadowLinDynamics import ShadowLinDynamics


class ShadowLinBase(ShadowLinDynamics, ShadowBase):
    def GeoDetectContact(self):
        """Run linear-base naive contact detection for every source."""
        return self.NaiveContactDetermination()

    def GeoPlanContactImpulses(self):
        return True

    def GeoResolveContacts(self):
        return True

    def NaiveContactDetermination(self):
        """Compare each source particle against every other particle.

        This is the intentionally simple O(N^2) contact-detection pass for the
        linear shadow base.  After one source has been compared to all possible
        targets, ContactDynamics() is called for that source.  For now,
        ContactDynamics() is a placeholder so we can build the linear flow one
        stage at a time.
        """
        position_buffer = int(self.ShaderFlags.positionBuffer)
        for source_id in range(len(self.particles)):
            for target_id in range(len(self.particles)):
                if source_id == target_id:
                    continue
                if self.isParticleContact(
                    self.ShaderFlags.frameNum,
                    source_id,
                    target_id,
                    position_buffer,
                ):
                    if not self.AddContactTargetID(source_id, target_id):
                        return False
                if self.collIn.ErrorReturn != self.constants.GEO_ERROR_NONE:
                    return False
            if not self.ContactDynamics(source_id):
                return False
        return True

    def AddContactTargetID(self, SourceID, TargetID):
        """Add only the target id to the source contact list."""
        source = self.particles[SourceID]
        if TargetID not in source.collision_list:
            source.collision_list.append(TargetID)
        return True

    def GeoMoveParticles(self):
        return self.Move()

    def Move(self):
        for SourceID in range(len(self.particles)):
            if not super().Move(SourceID):
                return False
        return True
