Considerations

1. The GPU has no dynmic memory allocation except local function memory.
	so the particle array, the cell array, and any other global memory cannot be
	dynmically allocated or expanded.
2. Two type of particle boundaries exist for now. 
	a .The first is a ghost boundary particle created when a collsion with a 
		mathematical boundary has been detected. 
	b The second is an actual particle in the particle list that has been 
		identified as a boundary particle. This particle type is fixed in the cell array
		at a cell where a boundary segment is located. When a collsion is detected with a
		boundary particle the mathmatics of that segment can be used to calculate resititution.
3. The current particle in any calulation is called the 'source' particle and the particle(s) against which
	it is being compared is the target particle.
4. Contact records should be fixed-size and typed.
	The GPU-friendly model is not to append target particles as they are discovered.
	Instead, each source particle owns a fixed-size contact list where each contact
	stores the target type plus the target data needed to evaluate that contact.
	Examples include a particle target, a wall target, or a boundary-segment target.
5. Wall geometry should return the same contact result shape as particle geometry.
	Whether the target is a real particle, a flat wall, a nozzle wall, or a boundary
	particle, the collision response should receive the same kind of contact data:
	normal_x, normal_y, overlap_area, and contact_distance. This lets the collision
	response stay generic while the geometry calculation changes by target type.
6. Exact overlap area for complex walls may become approximate.
	Circle-circle overlap is exact and inexpensive. Circle-vs-curved-wall or
	circle-vs-nozzle overlap may need to start as a penetration-depth approximation,
	then later improve to a segment-based or spline-based area model.
7. Presentation visuals should stay separate from physics state.
	Drawing blended overlap areas and collision normals is useful for explaining the
	idea to others, but those visual aids should not become required simulation state.
8. This is the glsl particle structure
--------------------------------------------------------------------------------------------
		struct lstr {
			uint pindex; 				// Index of cell the corner occupies.
			uint ploc;					// TBD.
			uint fill;					// fill.
		};
		struct bcoll {
			uint clflg;					// TBD.
		};
		struct ccoll {
			uint pindex;				// TBD.
			uint clflg;					// TBD.
		};
		// The particle structure.
		struct Particle {
			vec4  PosLocA; 				// First position buffer. x,y,z, hold the location and 1 stores the active flag. 0.0 if active, 1.0 if not.
			vec4  PosLocB;				// Second position buffer. x,y,z, hold the location and 1 stores the active flag. 0.0 if active, 1.0 if not.
			vec4  VelRad;				// Velocity, vx,vy,vz, store velocity angle in radians.
			vec4  Data;					// Particle Data x=particle radius, yzw not used.
			vec4  parms;				// x=mass, y=overlap momentum x, z=overlap momentum y, w=overlap momentum scalar sum.
			lstr  CornerList[8];		// Particle Corner List (see lstr).
			bcoll bcs[4];				// Current glsl version does not support walls. Only particle contacts.
			ccoll ccs[12];				// TBD
			uint  sltnum;				// Use to store contact count.
			uint  ColFlg;				// 1 if in collision, 0 if not.
			float MolarMatter;			// To be used later.
			float temp_vel;				// To be used later.
------------------------------------------------------------------------------------------------

9. 	The GPU code process is as follows:
	A. The compute phase iterates the over the corner list and retrieves the cell ID of the occupying cell.
	B. For each Cell ID, it calls 
		---------------------------------------------------
		if(isParticleContact(ii,SourceID, TargetID) > 0)
		....
		---------------------------------------------------
		for each particle which occupies the same cell.
	C. If the isParticleContact function returns true then the target paricle is checked to see if it is a duplicate.
	D. If not a duplicate it stores the collision in the ccs array and iterates sltnum to hold the collsion count.
	E. Once this loopl is finishged, the particle containes a colliding list which is then processed as a user function named
		ProcessCollision(uint SourceID)
10. The Particle.parms vector has a permanent dynamics mapping:
	parms.x stores source particle mass.
	parms.y stores overlap momentum x.
	parms.z stores overlap momentum y.
	parms.w stores the scalar sum of overlap momentum magnitudes.
		
