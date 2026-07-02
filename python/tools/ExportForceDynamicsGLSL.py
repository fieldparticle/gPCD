"""First gates for exporting ForceDynamics.py to GLSL.

By default this tool does not generate GLSL. It parses the Python dynamics
source, lists the methods available for export, and reports self-method calls
that are not defined in the export source. Known translation primitives are
allowed explicitly so hidden dependencies stay visible.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


DEFAULT_SOURCE = Path(__file__).resolve().parents[1] / "base" / "ForceDynamics.py"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[2]
    / "vulkan"
    / "sim"
    / "common"
    / "ForceDynamics.glsl"
)
DEFAULT_BOUNDARY_OUTPUT = DEFAULT_OUTPUT.with_name("ForceDynamicsBoundaryParticle.glsl")
DEFAULT_CD_NOZZLE_OUTPUT = DEFAULT_OUTPUT.with_name("ForceDynamicsCDNozzle.glsl")

KNOWN_TRANSLATION_PRIMITIVES = {
    "create_vec4": "Python vector factory; maps to vec4(...) in GLSL.",
}

GENERATED_GLSL_METHODS = [
    "VelocityAngle",
    "particle_position",
    "particle_overlap_area",
    "ParticleProximityMagnitude",
    "ParticlePenetrationDepth",
    "ProcessParticleCollision",
    "ProcessWallCollision",
    "IsBoundaryParticle",
    "BoundaryParticleWallFlag",
    "BoundaryParticleVerticalWallFlag",
    "BoundaryParticleCDNozzleWallFlag",
    "CDNozzleRadius",
    "CDNozzleRadiusSlope",
    "EvaluateWallSegment",
    "EvaluateHorizontalWallSegment",
    "EvaluateVerticalWallSegment",
    "EvaluateCDNozzleWallSegment",
    "ProcessBoundaryParticleWallCollision",
    "InitializeBoundaryParticleWallContactState",
    "InitializeWallContactState",
    "InitializeContactState",
    "GetContactState",
    "GetParticleGeometry",
    "GetParticlePosition",
    "StartingParticleKey",
    "StartingWallKey",
    "InitializeStartingContactState",
    "ParticleCenterDistance",
    "GetParticleEffectiveContactGeometry",
    "GetParticlePotentialGeometry",
    "AppendContactSlot",
    "GetContactSlots",
    "GetStartFrameVelocity",
    "AccumulateContactForce",
    "GetPairStiffness",
    "GetContactStiffness",
    "WallContactOffsetDistance",
    "GetPhysicalWallGhostGeometry",
    "GetWallGhostGeometry",
    "AppendWallContactSlot",
    "CheckPenetrationStepResolution",
    "ProjectSourceVelocityToContactSet",
    "ApplySourceMaximumDepth",
    "CalcVelocity",
    "GetParticleMass",
    "CalcPosition",
    "SetError",
]

BOUNDARY_PARTICLE_GLSL_METHODS = [
    "IsBoundaryParticle",
    "BoundaryParticleWallFlag",
    "BoundaryParticleVerticalWallFlag",
    "EvaluateHorizontalWallSegment",
    "EvaluateVerticalWallSegment",
    "ProcessBoundaryParticleWallCollision",
    "InitializeBoundaryParticleWallContactState",
]

CD_NOZZLE_GLSL_METHODS = [
    "BoundaryParticleCDNozzleWallFlag",
    "CDNozzleRadius",
    "CDNozzleRadiusSlope",
    "EvaluateCDNozzleWallSegment",
]

CORE_GLSL_METHODS = [
    method_name
    for method_name in GENERATED_GLSL_METHODS
    if method_name not in set(BOUNDARY_PARTICLE_GLSL_METHODS)
    and method_name not in set(CD_NOZZLE_GLSL_METHODS)
    and method_name != "EvaluateWallSegment"
]

PYTHON_WRAPPER_METHODS = [
    "isParticleContact",
    "DetectContacts",
    "NaiveContactDetermination",
    "AddContactTargetID",
    "BuildWallContactLists",
    "BoundaryParticleAppliesToSource",
    "BoundaryParticleWallsEnabled",
    "CalculateVelocities",
    "CalculatePositions",
]

CUSTOM_GLSL_HELPERS = [
    "IsParticleDead",
    "ApplyParticleDeathBounds",
    "GetParticleVelocity",
    "GetNextParticleVelocity",
    "SetNextParticleVelocity",
    "RegisterMaximumDepthConstraint",
    "SolveMaximumDepthSystem",
]

GLSL_SIGNATURES = {
    "VelocityAngle": "float VelocityAngle(float vx, float vy)",
    "particle_position": "vec4 particle_position(uint ParticleID, uint positionBuffer)",
    "particle_overlap_area": (
        "float particle_overlap_area(float source_radius, "
        "float target_radius, float center_distance)"
    ),
    "ParticleProximityMagnitude": (
        "float ParticleProximityMagnitude(float source_radius, "
        "float target_radius, float center_distance)"
    ),
    "ParticlePenetrationDepth": (
        "float ParticlePenetrationDepth(float source_radius, "
        "float target_radius, float center_distance)"
    ),
    "ProcessParticleCollision": (
        "bool ProcessParticleCollision(uint TargetID, uint SourceID, "
        "inout vec3 totalForce)"
    ),
    "ProcessWallCollision": (
        "bool ProcessWallCollision(uint SourceID, uint wall, inout vec3 totalForce)"
    ),
    "IsBoundaryParticle": "bool IsBoundaryParticle(uint ParticleID)",
    "BoundaryParticleWallFlag": (
        "uint BoundaryParticleWallFlag(uint SourceID, uint BoundaryID)"
    ),
    "BoundaryParticleVerticalWallFlag": (
        "uint BoundaryParticleVerticalWallFlag(uint SourceID, uint BoundaryID)"
    ),
    "BoundaryParticleCDNozzleWallFlag": (
        "uint BoundaryParticleCDNozzleWallFlag(uint SourceID, uint BoundaryID)"
    ),
    "CDNozzleRadius": "float CDNozzleRadius(float axial_position)",
    "CDNozzleRadiusSlope": "float CDNozzleRadiusSlope(float axial_position)",
    "EvaluateWallSegment": (
        "BoundaryWallSegment EvaluateWallSegment("
        "uint SourceID, uint BoundaryID)"
    ),
    "EvaluateHorizontalWallSegment": (
        "BoundaryWallSegment EvaluateHorizontalWallSegment("
        "uint SourceID, uint BoundaryID)"
    ),
    "EvaluateVerticalWallSegment": (
        "BoundaryWallSegment EvaluateVerticalWallSegment("
        "uint SourceID, uint BoundaryID)"
    ),
    "EvaluateCDNozzleWallSegment": (
        "BoundaryWallSegment EvaluateCDNozzleWallSegment("
        "uint SourceID, uint BoundaryID)"
    ),
    "ProcessBoundaryParticleWallCollision": (
        "bool ProcessBoundaryParticleWallCollision("
        "uint SourceID, uint BoundaryID, inout vec3 totalForce)"
    ),
    "InitializeBoundaryParticleWallContactState": (
        "bool InitializeBoundaryParticleWallContactState("
        "uint SourceID, uint BoundaryID)"
    ),
    "InitializeWallContactState": (
        "bool InitializeWallContactState(uint SourceID, uint wall)"
    ),
    "InitializeContactState": (
        "bool InitializeContactState(uint SourceID, uint TargetID)"
    ),
    "GetContactState": "bool GetContactState(uint SourceID, uint TargetID)",
    "GetParticleGeometry": (
        "ParticleGeometry GetParticleGeometry(uint SourceID, uint TargetID)"
    ),
    "GetParticlePosition": "vec4 GetParticlePosition(uint ParticleID)",
    "StartingParticleKey": "uint StartingParticleKey(uint SourceID, uint TargetID)",
    "StartingWallKey": "uint StartingWallKey(uint SourceID, uint wall_flag)",
    "InitializeStartingContactState": "void InitializeStartingContactState()",
    "ParticleCenterDistance": (
        "float ParticleCenterDistance(uint SourceID, uint TargetID)"
    ),
    "GetParticleEffectiveContactGeometry": (
        "ParticleEffectiveContactGeometry GetParticleEffectiveContactGeometry("
        "uint SourceID, uint TargetID, float center_distance)"
    ),
    "GetParticlePotentialGeometry": (
        "ParticlePotentialGeometry GetParticlePotentialGeometry("
        "uint SourceID, uint TargetID, float center_distance)"
    ),
    "AppendContactSlot": "bool AppendContactSlot(uint SourceID, uint TargetID)",
    "GetContactSlots": "uint GetContactSlots(uint SourceID)",
    "GetStartFrameVelocity": "vec4 GetStartFrameVelocity(uint ParticleID)",
    "GetParticleVelocity": "vec4 GetParticleVelocity(uint ParticleID)",
    "GetNextParticleVelocity": "vec4 GetNextParticleVelocity(uint ParticleID)",
    "SetNextParticleVelocity": (
        "void SetNextParticleVelocity(uint ParticleID, vec4 velocity)"
    ),
    "AccumulateContactForce": (
        "bool AccumulateContactForce("
        "uint SourceID, ContactForceInput contact, inout vec3 totalForce)"
    ),
    "GetPairStiffness": "float GetPairStiffness(uint SourceID, uint TargetID)",
    "GetContactStiffness": (
        "float GetContactStiffness(uint SourceID, uint TargetID, uint contact_type)"
    ),
    "WallContactOffsetDistance": "float WallContactOffsetDistance(float radius)",
    "GetPhysicalWallGhostGeometry": (
        "WallPhysicalGhostGeometry GetPhysicalWallGhostGeometry("
        "uint SourceID, uint wall_flag)"
    ),
    "GetWallGhostGeometry": (
        "WallGhostGeometry GetWallGhostGeometry(uint SourceID, uint wall_flag)"
    ),
    "AppendWallContactSlot": (
        "bool AppendWallContactSlot(uint SourceID, uint wall_flag)"
    ),
    "CheckPenetrationStepResolution": (
        "bool CheckPenetrationStepResolution(uint SourceID, vec3 normal, "
        "float source_radius, vec3 target_velocity)"
    ),
    "ProjectSourceVelocityToContactSet": (
        "bool ProjectSourceVelocityToContactSet("
        "vec3 candidate_velocity, out vec3 contained_velocity)"
    ),
    "ApplySourceMaximumDepth": "bool ApplySourceMaximumDepth(uint SourceID)",
    "CalcVelocity": "bool CalcVelocity(uint SourceID, vec3 totalForce)",
    "GetParticleMass": "float GetParticleMass(uint ParticleID)",
    "CalcPosition": "bool CalcPosition(uint SourceID)",
    "StartReservoir": "bool StartReservoir(uint SourceID)",
    "RetireParticlePastXMax": "bool RetireParticlePastXMax(uint SourceID)",
    "RetireParticleAtCellGuard": "bool RetireParticleAtCellGuard(uint SourceID)",
    "SetError": "bool SetError(uint error_code)",
    "IsParticleDead": "bool IsParticleDead(uint ParticleID)",
    "ApplyParticleDeathBounds": (
        "bool ApplyParticleDeathBounds(uint ParticleID)"
    ),
    "RegisterMaximumDepthConstraint": (
        "bool RegisterMaximumDepthConstraint("
        "uint SourceID, vec3 normal, float penetration_depth, float source_radius)"
    ),
    "SolveMaximumDepthSystem": (
        "bool SolveMaximumDepthSystem("
        "mat3 matrix, vec3 values, uint size, out vec3 solution)"
    ),
}

GLSL_DEFAULT_RETURNS = {
    "bool": "false",
    "float": "0.0",
    "uint": "0u",
    "vec4": "vec4(0.0)",
    "ParticleEffectiveContactGeometry": "ParticleEffectiveContactGeometry(0.0, 0.0, 0.0, 0.0, 0.0, false)",
    "ParticleGeometry": "ParticleGeometry(vec3(0.0), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, false)",
    "ParticlePotentialGeometry": "ParticlePotentialGeometry(0.0, 0.0, false)",
    "WallPhysicalGhostGeometry": "WallPhysicalGhostGeometry(vec3(0.0), 0.0, 0.0, false)",
    "WallGhostGeometry": "WallGhostGeometry(vec3(0.0), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, false)",
    "BoundaryWallSegment": "BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false)",
}

GLSL_RESULT_STRUCTS = [
    (
        "ParticleEffectiveContactGeometry",
        [
            "float sourceRadius;",
            "float targetRadius;",
            "float physicalSeparationLimit;",
            "float startingContact;",
            "float startingResolved;",
            "bool suppressContact;",
        ],
    ),
    (
        "ParticleGeometry",
        [
            "vec3 normal;",
            "float overlapArea;",
            "float centerDistance;",
            "float effectiveSourceRadius;",
            "float effectiveTargetRadius;",
            "float physicalSeparationLimit;",
            "float startingContact;",
            "float startingResolved;",
            "bool valid;",
        ],
    ),
    (
        "ParticlePotentialGeometry",
        [
            "float sourceRadius;",
            "float targetRadius;",
            "bool valid;",
        ],
    ),
    (
        "WallPhysicalGhostGeometry",
        [
            "vec3 normal;",
            "float overlapArea;",
            "float centerDistance;",
            "bool valid;",
        ],
    ),
    (
        "WallGhostGeometry",
        [
            "vec3 normal;",
            "float overlapArea;",
            "float centerDistance;",
            "float effectiveRadius;",
            "float physicalSeparationLimit;",
            "float startingContact;",
            "float startingResolved;",
            "bool valid;",
        ],
    ),
    (
        "BoundaryWallSegment",
        [
            "vec3 normal;",
            "float overlapArea;",
            "float centerDistance;",
            "uint wallFlag;",
            "bool valid;",
        ],
    ),
    (
        "ContactForceInput",
        [
            "uint targetID;",
            "uint contactType;",
            "vec3 normal;",
            "float overlapArea;",
            "float penetrationDepth;",
            "bool valid;",
        ],
    ),
]

TRANSLATION_STATUS = {
    "direct": [
        "VelocityAngle",
        "particle_position",
        "particle_overlap_area",
        "GetParticlePosition",
        "ParticleCenterDistance",
        "GetStartFrameVelocity",
        "GetPairStiffness",
        "GetContactStiffness",
        "WallContactOffsetDistance",
        "GetParticleMass",
        "CheckPenetrationStepResolution",
        "ProjectSourceVelocityToContactSet",
        "ApplySourceMaximumDepth",
        "CalcVelocity",
        "CalcPosition",
        "AccumulateContactForce",
        "ProcessParticleCollision",
        "ProcessWallCollision",
        "IsBoundaryParticle",
        "BoundaryParticleWallFlag",
        "BoundaryParticleVerticalWallFlag",
        "BoundaryParticleCDNozzleWallFlag",
        "CDNozzleRadius",
        "CDNozzleRadiusSlope",
        "ParticleProximityMagnitude",
        "ParticlePenetrationDepth",
        "ProcessBoundaryParticleWallCollision",
        "SetError",
    ],
    "needs_struct": [
        "GetParticleGeometry",
        "GetParticleEffectiveContactGeometry",
        "GetParticlePotentialGeometry",
        "GetPhysicalWallGhostGeometry",
        "GetWallGhostGeometry",
        "EvaluateWallSegment",
        "EvaluateHorizontalWallSegment",
        "EvaluateVerticalWallSegment",
        "EvaluateCDNozzleWallSegment",
    ],
    "needs_buffer": [
        "StartingParticleKey",
        "StartingWallKey",
        "InitializeStartingContactState",
    ],
    "defer": [
        "InitializeWallContactState",
        "InitializeContactState",
        "GetContactState",
        "AppendContactSlot",
        "GetContactSlots",
        "AppendWallContactSlot",
        "InitializeBoundaryParticleWallContactState",
    ],
}

TRANSLATION_STATUS_DESCRIPTIONS = {
    "direct": "can be translated nearly 1:1 now",
    "needs_struct": "needs a GLSL result struct or temporary state object",
    "needs_buffer": "depends on StartingContactState or particle/storage layout",
    "defer": "depends on later interface decisions",
}

TEMPLATE_GENERATED_METHODS = {
    "VelocityAngle",
    "particle_position",
    "particle_overlap_area",
    "ParticleProximityMagnitude",
    "ParticlePenetrationDepth",
    "GetParticlePosition",
    "ParticleCenterDistance",
    "GetParticleGeometry",
    "GetParticleEffectiveContactGeometry",
    "GetParticlePotentialGeometry",
    "GetStartFrameVelocity",
    "GetPairStiffness",
    "GetContactStiffness",
    "WallContactOffsetDistance",
    "GetParticleMass",
    "CheckPenetrationStepResolution",
    "ProjectSourceVelocityToContactSet",
    "ApplySourceMaximumDepth",
    "CalcVelocity",
    "CalcPosition",
    "GetPhysicalWallGhostGeometry",
    "GetWallGhostGeometry",
    "IsBoundaryParticle",
    "BoundaryParticleWallFlag",
    "BoundaryParticleVerticalWallFlag",
    "BoundaryParticleCDNozzleWallFlag",
    "CDNozzleRadius",
    "CDNozzleRadiusSlope",
    "EvaluateWallSegment",
    "EvaluateHorizontalWallSegment",
    "EvaluateVerticalWallSegment",
    "EvaluateCDNozzleWallSegment",
    "ProcessBoundaryParticleWallCollision",
    "SetError",
}

GLSL_BODY_TEMPLATES = {
    "VelocityAngle": [
        "return (vx != 0.0 || vy != 0.0) ? atan(vy, vx) : 0.0;",
    ],
    "particle_position": [
        "return (positionBuffer == 0u)",
        "    ? P[ParticleID].PosLocA",
        "    : P[ParticleID].PosLocB;",
    ],
    "particle_overlap_area": [
        "if (center_distance <= 0.0) {",
        "    float min_radius = min(source_radius, target_radius);",
        "    return FORCE_DYNAMICS_PI * min_radius * min_radius;",
        "}",
        "if (center_distance >= source_radius + target_radius) {",
        "    return 0.0;",
        "}",
        "if (center_distance <= abs(source_radius - target_radius)) {",
        "    float min_radius = min(source_radius, target_radius);",
        "    return FORCE_DYNAMICS_PI * min_radius * min_radius;",
        "}",
        "",
        "float source_term = (",
        "    center_distance * center_distance",
        "    + source_radius * source_radius",
        "    - target_radius * target_radius",
        ") / (2.0 * center_distance * source_radius);",
        "float target_term = (",
        "    center_distance * center_distance",
        "    + target_radius * target_radius",
        "    - source_radius * source_radius",
        ") / (2.0 * center_distance * target_radius);",
        "source_term = clamp(source_term, -1.0, 1.0);",
        "target_term = clamp(target_term, -1.0, 1.0);",
        "float source_area = source_radius * source_radius * acos(source_term);",
        "float target_area = target_radius * target_radius * acos(target_term);",
        "float triangle_area = 0.5 * sqrt(max(",
        "    0.0,",
        "    (-center_distance + source_radius + target_radius)",
        "    * (center_distance + source_radius - target_radius)",
        "    * (center_distance - source_radius + target_radius)",
        "    * (center_distance + source_radius + target_radius)",
        "));",
        "return source_area + target_area - triangle_area;",
    ],
    "ParticleProximityMagnitude": [
        "return max(0.0, center_distance - target_radius);",
    ],
    "ParticlePenetrationDepth": [
        "float orientation_magnitude = source_radius;",
        "float proximity_magnitude = ParticleProximityMagnitude(",
        "    source_radius,",
        "    target_radius,",
        "    center_distance",
        ");",
        "return orientation_magnitude - proximity_magnitude;",
    ],
    "ProcessParticleCollision": [
        "ParticleGeometry geometry = GetParticleGeometry(SourceID, TargetID);",
        "if (!geometry.valid) {",
        "    return true;",
        "}",
        "float penetration_depth = ParticlePenetrationDepth(",
        "    geometry.effectiveSourceRadius,",
        "    geometry.effectiveTargetRadius,",
        "    geometry.centerDistance",
        ");",
        "float directed_proximity = geometry.centerDistance",
        "    - geometry.effectiveTargetRadius;",
        "if (directed_proximity < -EPSILON) {",
        "    return SetError(ERROR_PARTICLE_TUNNELING);",
        "}",
        "if (!CheckPenetrationStepResolution(",
        "        SourceID, geometry.normal, geometry.effectiveSourceRadius,",
        "        GetStartFrameVelocity(TargetID).xyz)) {",
        "    return false;",
        "}",
        "if (!RegisterMaximumDepthConstraint(",
        "        SourceID, geometry.normal, penetration_depth,",
        "        geometry.effectiveSourceRadius)) {",
        "    return false;",
        "}",
        "ContactForceInput contact = ContactForceInput(",
        "    TargetID,",
        "    CONTACT_PARTICLE,",
        "    geometry.normal,",
        "    geometry.overlapArea,",
        "    penetration_depth,",
        "    geometry.valid",
        ");",
        "return AccumulateContactForce(SourceID, contact, totalForce);",
    ],
    "ProcessWallCollision": [
        "WallGhostGeometry geometry = GetWallGhostGeometry(SourceID, wall);",
        "if (!geometry.valid) {",
        "    return true;",
        "}",
        "float penetration_depth = ParticlePenetrationDepth(",
        "    geometry.effectiveRadius,",
        "    geometry.effectiveRadius,",
        "    geometry.centerDistance",
        ");",
        "float maximum_depth_distance = geometry.effectiveRadius",
        "    - WallContactOffsetDistance(geometry.effectiveRadius);",
        "if (geometry.centerDistance - maximum_depth_distance < -EPSILON) {",
        "    return SetError(ERROR_WALL_TUNNELING);",
        "}",
        "if (!CheckPenetrationStepResolution(",
        "        SourceID, geometry.normal, geometry.effectiveRadius, vec3(0.0))) {",
        "    return false;",
        "}",
        "if (!RegisterMaximumDepthConstraint(",
        "        SourceID, geometry.normal, penetration_depth,",
        "        geometry.effectiveRadius)) {",
        "    return false;",
        "}",
        "ContactForceInput contact = ContactForceInput(",
        "    wall,",
        "    CONTACT_WALL,",
        "    geometry.normal,",
        "    geometry.overlapArea,",
        "    penetration_depth,",
        "    geometry.valid",
        ");",
        "return AccumulateContactForce(SourceID, contact, totalForce);",
    ],
    "IsBoundaryParticle": [
        "return P[ParticleID].ptype > 0.5;",
    ],
    "BoundaryParticleWallFlag": [
        "if (!IsBoundaryParticle(BoundaryID)) {",
        "    return 0u;",
        "}",
        "",
        "vec4 boundary_position = GetParticlePosition(BoundaryID);",
        "float mid_y = 0.5 * (BOUNDARY_YMIN + BOUNDARY_YMAX);",
        "return (boundary_position.y < mid_y) ? 3u : 4u;",
    ],
    "BoundaryParticleVerticalWallFlag": [
        "if (!IsBoundaryParticle(BoundaryID)) {",
        "    return 0u;",
        "}",
        "",
        "vec4 boundary_position = GetParticlePosition(BoundaryID);",
        "float mid_x = 0.5 * (BOUNDARY_XMIN + BOUNDARY_XMAX);",
        "return (boundary_position.x < mid_x) ? 1u : 2u;",
    ],
    "BoundaryParticleCDNozzleWallFlag": [
        "if (!IsBoundaryParticle(BoundaryID)) {",
        "    return 0u;",
        "}",
        "",
        "vec4 boundary_position = GetParticlePosition(BoundaryID);",
        "return (boundary_position.y < CD_NOZZLE_CENTER_Y) ? 3u : 4u;",
    ],
    "CDNozzleRadius": [
        "float inlet_end = CD_NOZZLE_INLET_LENGTH;",
        "float converge_end = inlet_end + CD_NOZZLE_CONVERGE_LENGTH;",
        "float throat_end = converge_end + CD_NOZZLE_THROAT_LENGTH;",
        "float diverge_end = throat_end + CD_NOZZLE_DIVERGE_LENGTH;",
        "",
        "if (axial_position >= 1.0 && axial_position < inlet_end) {",
        "    return CD_NOZZLE_INLET_RADIUS;",
        "}",
        "if (axial_position >= inlet_end && axial_position < converge_end) {",
        "    float span = max(CD_NOZZLE_CONVERGE_LENGTH, EPSILON);",
        "    float throat_distance = converge_end - axial_position;",
        "    float t = throat_distance / span;",
        "    return CD_NOZZLE_THROAT_RADIUS",
        "        + (CD_NOZZLE_INLET_RADIUS - CD_NOZZLE_THROAT_RADIUS)",
        "        * t * t;",
        "}",
        "if (axial_position >= converge_end && axial_position < throat_end) {",
        "    return CD_NOZZLE_THROAT_RADIUS;",
        "}",
        "if (axial_position >= throat_end && axial_position < diverge_end) {",
        "    float span = max(CD_NOZZLE_DIVERGE_LENGTH, EPSILON);",
        "    float t = (axial_position - throat_end) / span;",
        "    return CD_NOZZLE_THROAT_RADIUS",
        "        + (CD_NOZZLE_EXIT_RADIUS - CD_NOZZLE_THROAT_RADIUS)",
        "        * t * t;",
        "}",
        "if (axial_position >= diverge_end) {",
        "    return CD_NOZZLE_EXIT_RADIUS;",
        "}",
        "return CD_NOZZLE_INLET_RADIUS;",
    ],
    "CDNozzleRadiusSlope": [
        "float inlet_end = CD_NOZZLE_INLET_LENGTH;",
        "float converge_end = inlet_end + CD_NOZZLE_CONVERGE_LENGTH;",
        "float throat_end = converge_end + CD_NOZZLE_THROAT_LENGTH;",
        "float diverge_end = throat_end + CD_NOZZLE_DIVERGE_LENGTH;",
        "",
        "if (axial_position >= inlet_end && axial_position < converge_end) {",
        "    float span = max(CD_NOZZLE_CONVERGE_LENGTH, EPSILON);",
        "    float throat_distance = converge_end - axial_position;",
        "    return -2.0",
        "        * (CD_NOZZLE_INLET_RADIUS - CD_NOZZLE_THROAT_RADIUS)",
        "        * throat_distance / (span * span);",
        "}",
        "if (axial_position >= throat_end && axial_position < diverge_end) {",
        "    float span = max(CD_NOZZLE_DIVERGE_LENGTH, EPSILON);",
        "    float throat_distance = axial_position - throat_end;",
        "    return 2.0",
        "        * (CD_NOZZLE_EXIT_RADIUS - CD_NOZZLE_THROAT_RADIUS)",
        "        * throat_distance / (span * span);",
        "}",
        "return 0.0;",
    ],
    "EvaluateWallSegment": [
        "uint evaluator_id = uint(round(P[BoundaryID].Data.z));",
        "if (evaluator_id == 1u) {",
        "    return EvaluateHorizontalWallSegment(SourceID, BoundaryID);",
        "}",
        "if (evaluator_id == 2u) {",
        "    return EvaluateVerticalWallSegment(SourceID, BoundaryID);",
        "}",
        "if (evaluator_id == 3u) {",
        "#if defined(FORCE_DYNAMICS_CD_NOZZLE_AVAILABLE)",
        "    return EvaluateCDNozzleWallSegment(SourceID, BoundaryID);",
        "#else",
        "    return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);",
        "#endif",
        "}",
        "return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);",
    ],
    "EvaluateHorizontalWallSegment": [
        "uint wall_flag = BoundaryParticleWallFlag(SourceID, BoundaryID);",
        "if (wall_flag == 0u) {",
        "    return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);",
        "}",
        "",
        "vec4 source_position = GetParticlePosition(SourceID);",
        "vec4 boundary_position = GetParticlePosition(BoundaryID);",
        "float radius = P[SourceID].Data.x;",
        "float offset = WallContactOffsetDistance(radius);",
        "vec3 ghost = vec3(0.0);",
        "vec3 normal = vec3(0.0);",
        "",
        "if (wall_flag == 3u) {",
        "    ghost = vec3(source_position.x, boundary_position.y - radius + offset, source_position.z);",
        "    normal = vec3(0.0, -1.0, 0.0);",
        "} else if (wall_flag == 4u) {",
        "    ghost = vec3(source_position.x, boundary_position.y + radius - offset, source_position.z);",
        "    normal = vec3(0.0, 1.0, 0.0);",
        "} else {",
        "    return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, wall_flag, false);",
        "}",
        "",
        "vec3 delta = ghost - source_position.xyz;",
        "float center_distance = length(delta);",
        "if (center_distance >= 2.0 * radius) {",
        "    return BoundaryWallSegment(normal, 0.0, center_distance, wall_flag, false);",
        "}",
        "",
        "float overlap_area = particle_overlap_area(radius, radius, center_distance);",
        "return BoundaryWallSegment(normal, overlap_area, center_distance, wall_flag, true);",
    ],
    "EvaluateVerticalWallSegment": [
        "uint wall_flag = BoundaryParticleVerticalWallFlag(SourceID, BoundaryID);",
        "if (wall_flag == 0u) {",
        "    return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);",
        "}",
        "",
        "vec4 source_position = GetParticlePosition(SourceID);",
        "vec4 boundary_position = GetParticlePosition(BoundaryID);",
        "float radius = P[SourceID].Data.x;",
        "float offset = WallContactOffsetDistance(radius);",
        "vec3 ghost = vec3(0.0);",
        "vec3 normal = vec3(0.0);",
        "",
        "if (wall_flag == 1u) {",
        "    ghost = vec3(boundary_position.x - radius + offset, source_position.y, source_position.z);",
        "    normal = vec3(-1.0, 0.0, 0.0);",
        "} else if (wall_flag == 2u) {",
        "    ghost = vec3(boundary_position.x + radius - offset, source_position.y, source_position.z);",
        "    normal = vec3(1.0, 0.0, 0.0);",
        "} else {",
        "    return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, wall_flag, false);",
        "}",
        "",
        "vec3 delta = ghost - source_position.xyz;",
        "float center_distance = length(delta);",
        "if (center_distance >= 2.0 * radius) {",
        "    return BoundaryWallSegment(normal, 0.0, center_distance, wall_flag, false);",
        "}",
        "",
        "float overlap_area = particle_overlap_area(radius, radius, center_distance);",
        "return BoundaryWallSegment(normal, overlap_area, center_distance, wall_flag, true);",
    ],
    "EvaluateCDNozzleWallSegment": [
        "uint wall_flag = BoundaryParticleCDNozzleWallFlag(SourceID, BoundaryID);",
        "if (wall_flag == 0u) {",
        "    return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, 0u, false);",
        "}",
        "",
        "vec4 source_position = GetParticlePosition(SourceID);",
        "float radius = P[SourceID].Data.x;",
        "float axial = source_position.x - CD_NOZZLE_START_X + 1.0;",
        "float total_length = CD_NOZZLE_INLET_LENGTH",
        "    + CD_NOZZLE_CONVERGE_LENGTH",
        "    + CD_NOZZLE_THROAT_LENGTH",
        "    + CD_NOZZLE_DIVERGE_LENGTH",
        "    + CD_NOZZLE_EXIT_LENGTH;",
        "if (axial < 1.0 || axial > total_length) {",
        "    return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, wall_flag, false);",
        "}",
        "",
        "float nozzle_radius = CDNozzleRadius(axial);",
        "float radius_slope = CDNozzleRadiusSlope(axial);",
        "float offset = WallContactOffsetDistance(radius);",
        "float wall_y = 0.0;",
        "vec3 normal = vec3(0.0);",
        "",
        "if (wall_flag == 3u) {",
        "    wall_y = CD_NOZZLE_CENTER_Y - nozzle_radius;",
        "    normal = normalize(vec3(-radius_slope, -1.0, 0.0));",
        "} else if (wall_flag == 4u) {",
        "    wall_y = CD_NOZZLE_CENTER_Y + nozzle_radius;",
        "    normal = normalize(vec3(-radius_slope, 1.0, 0.0));",
        "} else {",
        "    return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, wall_flag, false);",
        "}",
        "",
        "vec3 wall_point = vec3(source_position.x, wall_y, source_position.z);",
        "vec3 ghost = wall_point + normal * (radius - offset);",
        "vec3 delta = ghost - source_position.xyz;",
        "float center_distance = length(delta);",
        "if (center_distance >= 2.0 * radius) {",
        "    return BoundaryWallSegment(normal, 0.0, center_distance, wall_flag, false);",
        "}",
        "",
        "float overlap_area = particle_overlap_area(radius, radius, center_distance);",
        "return BoundaryWallSegment(normal, overlap_area, center_distance, wall_flag, true);",
    ],
    "ProcessBoundaryParticleWallCollision": [
        "BoundaryWallSegment segment = EvaluateWallSegment(SourceID, BoundaryID);",
        "if (!segment.valid) {",
        "    return true;",
        "}",
        "float source_radius = P[SourceID].Data.x;",
        "float penetration_depth = ParticlePenetrationDepth(",
        "    source_radius, source_radius, segment.centerDistance);",
        "float maximum_depth_distance = source_radius",
        "    - WallContactOffsetDistance(source_radius);",
        "if (segment.centerDistance - maximum_depth_distance < -EPSILON) {",
        "    return SetError(ERROR_WALL_TUNNELING);",
        "}",
        "if (!CheckPenetrationStepResolution(",
        "        SourceID, segment.normal, source_radius, vec3(0.0))) {",
        "    return false;",
        "}",
        "if (!RegisterMaximumDepthConstraint(",
        "        SourceID, segment.normal, penetration_depth, source_radius)) {",
        "    return false;",
        "}",
        "ContactForceInput contact = ContactForceInput(",
        "    segment.wallFlag,",
        "    CONTACT_WALL,",
        "    segment.normal,",
        "    segment.overlapArea,",
        "    penetration_depth,",
        "    segment.valid",
        ");",
        "return AccumulateContactForce(SourceID, contact, totalForce);",
    ],
    "GetParticlePosition": [
        "return particle_position(ParticleID, uint(ShaderFlags.positionBuffer));",
    ],
    "ParticleCenterDistance": [
        "vec4 source_position = GetParticlePosition(SourceID);",
        "vec4 target_position = GetParticlePosition(TargetID);",
        "vec3 delta = target_position.xyz - source_position.xyz;",
        "return length(delta);",
    ],
    "GetParticleGeometry": [
        "vec4 source_position = GetParticlePosition(SourceID);",
        "vec4 target_position = GetParticlePosition(TargetID);",
        "vec3 delta = target_position.xyz - source_position.xyz;",
        "float center_distance = length(delta);",
        "",
        "ParticleEffectiveContactGeometry effective =",
        "    GetParticleEffectiveContactGeometry(SourceID, TargetID, center_distance);",
        "if (effective.suppressContact) {",
        "    return ParticleGeometry(vec3(0.0), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, false);",
        "}",
        "if (center_distance >= effective.sourceRadius + effective.targetRadius) {",
        "    return ParticleGeometry(vec3(0.0), 0.0, center_distance, effective.sourceRadius, effective.targetRadius, effective.physicalSeparationLimit, effective.startingContact, effective.startingResolved, false);",
        "}",
        "",
        "vec3 normal = (center_distance <= EPSILON)",
        "    ? vec3(1.0, 0.0, 0.0)",
        "    : delta / center_distance;",
        "float overlap_area = particle_overlap_area(",
        "    effective.sourceRadius,",
        "    effective.targetRadius,",
        "    center_distance",
        ");",
        "return ParticleGeometry(",
        "    normal,",
        "    overlap_area,",
        "    center_distance,",
        "    effective.sourceRadius,",
        "    effective.targetRadius,",
        "    effective.physicalSeparationLimit,",
        "    effective.startingContact,",
        "    effective.startingResolved,",
        "    true",
        ");",
    ],
    "GetParticleEffectiveContactGeometry": [
        "float source_radius = P[SourceID].Data.x;",
        "float target_radius = P[TargetID].Data.x;",
        "float physical_limit = source_radius + target_radius;",
        "",
        "// Step 6 ordinary-contact fallback: starting-contact effective radii",
        "// are added later through StartingContactState buffer logic.",
        "return ParticleEffectiveContactGeometry(",
        "    source_radius,",
        "    target_radius,",
        "    physical_limit,",
        "    0.0,",
        "    0.0,",
        "    false",
        ");",
    ],
    "GetParticlePotentialGeometry": [
        "ParticleEffectiveContactGeometry effective =",
        "    GetParticleEffectiveContactGeometry(SourceID, TargetID, center_distance);",
        "if (effective.suppressContact) {",
        "    return ParticlePotentialGeometry(0.0, 0.0, false);",
        "}",
        "if (center_distance >= effective.sourceRadius + effective.targetRadius) {",
        "    return ParticlePotentialGeometry(effective.sourceRadius, effective.targetRadius, false);",
        "}",
        "return ParticlePotentialGeometry(effective.sourceRadius, effective.targetRadius, true);",
    ],
    "GetStartFrameVelocity": [
        "return GetParticleVelocity(ParticleID);",
    ],
    "GetParticleVelocity": [
        "return (uint(ShaderFlags.positionBuffer) == 0u)",
        "    ? P[ParticleID].VelRadA",
        "    : P[ParticleID].VelRadB;",
    ],
    "IsParticleDead": [
        "return P[ParticleID].Data.w < 0.0;",
    ],
    "ApplyParticleDeathBounds": [
        "if (P[ParticleID].ptype > 0.5) {",
        "    return true;",
        "}",
        "vec4 next_position = (uint(ShaderFlags.positionBuffer) == 0u)",
        "    ? P[ParticleID].PosLocB",
        "    : P[ParticleID].PosLocA;",
        "if (next_position.x < death_x_min",
        "        || next_position.x > death_x_max",
        "        || next_position.y < death_y_min",
        "        || next_position.y > death_y_max",
        "        || next_position.z < death_z_min",
        "        || next_position.z > death_z_max) {",
        "    P[ParticleID].Data.w = -1.0;",
        "    return false;",
        "}",
        "return true;",
    ],
    "GetNextParticleVelocity": [
        "return (uint(ShaderFlags.positionBuffer) == 0u)",
        "    ? P[ParticleID].VelRadB",
        "    : P[ParticleID].VelRadA;",
    ],
    "SetNextParticleVelocity": [
        "if (uint(ShaderFlags.positionBuffer) == 0u) {",
        "    P[ParticleID].VelRadB = velocity;",
        "} else {",
        "    P[ParticleID].VelRadA = velocity;",
        "}",
    ],
    "GetPairStiffness": [
        "float source_q = P[SourceID].Data.y;",
        "float target_q = P[TargetID].Data.y;",
        "return max(0.0, 0.5 * (source_q + target_q));",
    ],
    "GetContactStiffness": [
        "if (contact_type == CONTACT_WALL) {",
        "    return max(0.0, P[SourceID].Data.y);",
        "}",
        "return GetPairStiffness(SourceID, TargetID);",
    ],
    "AccumulateContactForce": [
        "if (!contact.valid) {",
        "    return true;",
        "}",
        "",
        "float stiffness = GetContactStiffness(",
        "    SourceID,",
        "    contact.targetID,",
        "    contact.contactType",
        ");",
        "#if defined(CONTACT_FORCE_MEASURE) && CONTACT_FORCE_MEASURE == depth",
        "float contact_measure = contact.penetrationDepth;",
        "#else",
        "float contact_measure = contact.overlapArea;",
        "#endif",
        "float force_magnitude = stiffness * max(0.0, contact_measure);",
        "float impulse = force_magnitude * ShaderFlags.dt;",
        "vec3 source_velocity = GetParticleVelocity(SourceID).xyz;",
        "vec3 target_velocity = (contact.contactType == CONTACT_WALL)",
        "    ? vec3(0.0)",
        "    : GetParticleVelocity(contact.targetID).xyz;",
        "float rel_vn = dot(target_velocity - source_velocity, contact.normal);",
        "vec3 internal_momentum = P[SourceID].parms.yzw;",
        "if (rel_vn < -EPSILON) {",
        "    internal_momentum += impulse * contact.normal;",
        "} else if (rel_vn > EPSILON) {",
        "    float stored_along_normal = dot(internal_momentum, contact.normal);",
        "    float release_impulse = min(max(0.0, stored_along_normal), impulse);",
        "    internal_momentum -= release_impulse * contact.normal;",
        "}",
        "P[SourceID].parms.yzw = internal_momentum;",
        "P[SourceID].Data.z = length(internal_momentum);",
        "totalForce.x -= force_magnitude * contact.normal.x;",
        "totalForce.y -= force_magnitude * contact.normal.y;",
        "totalForce.z -= force_magnitude * contact.normal.z;",
        "return true;",
    ],
    "WallContactOffsetDistance": [
        "return min(radius, radius * wall_contact_offset);",
    ],
    "GetParticleMass": [
        "return max(P[ParticleID].parms.x, EPSILON);",
    ],
    "CheckPenetrationStepResolution": [
        "vec3 source_velocity = GetStartFrameVelocity(SourceID).xyz;",
        "float relative_normal_velocity = dot(",
        "    target_velocity - source_velocity, normal);",
        "float inward_displacement = max(",
        "    0.0, -relative_normal_velocity * ShaderFlags.dt);",
        "float penetration_reserve =",
        "    (1.0 - MAXIMUM_PENETRATION_FRACTION) * source_radius;",
        "if (inward_displacement > penetration_reserve + EPSILON) {",
        "    return SetError(ERROR_PENETRATION_STEP_TOO_LARGE);",
        "}",
        "return true;",
    ],
    "ProjectSourceVelocityToContactSet": [
        "contained_velocity = candidate_velocity;",
        "bool candidate_valid = true;",
        "for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {",
        "    if (dot(maximumDepthConstraintNormals[index], candidate_velocity)",
        "            > maximumDepthConstraintLimits[index] + EPSILON) {",
        "        candidate_valid = false;",
        "    }",
        "}",
        "if (candidate_valid) {",
        "    return true;",
        "}",
        "",
        "bool found = false;",
        "float best_distance_sq = 0.0;",
        "for (uint i = 0u; i < maximumDepthConstraintCount; ++i) {",
        "    for (uint j_code = 0u; j_code <= maximumDepthConstraintCount; ++j_code) {",
        "        for (uint k_code = 0u; k_code <= maximumDepthConstraintCount; ++k_code) {",
        "            uint active_count = 1u;",
        "            uint j = 0u;",
        "            uint k = 0u;",
        "            if (j_code > 0u) {",
        "                j = j_code - 1u;",
        "                if (j <= i) { continue; }",
        "                active_count = 2u;",
        "            } else if (k_code > 0u) {",
        "                continue;",
        "            }",
        "            if (k_code > 0u) {",
        "                k = k_code - 1u;",
        "                if (active_count != 2u || k <= j) { continue; }",
        "                active_count = 3u;",
        "            }",
        "",
        "            vec3 n0 = maximumDepthConstraintNormals[i];",
        "            vec3 n1 = active_count >= 2u",
        "                ? maximumDepthConstraintNormals[j] : vec3(0.0);",
        "            vec3 n2 = active_count >= 3u",
        "                ? maximumDepthConstraintNormals[k] : vec3(0.0);",
        "            vec3 limits = vec3(",
        "                maximumDepthConstraintLimits[i],",
        "                active_count >= 2u ? maximumDepthConstraintLimits[j] : 0.0,",
        "                active_count >= 3u ? maximumDepthConstraintLimits[k] : 0.0);",
        "            mat3 gram = mat3(0.0);",
        "            gram[0][0] = dot(n0, n0);",
        "            if (active_count >= 2u) {",
        "                gram[0][1] = dot(n0, n1);",
        "                gram[1][0] = gram[0][1];",
        "                gram[1][1] = dot(n1, n1);",
        "            }",
        "            if (active_count >= 3u) {",
        "                gram[0][2] = dot(n0, n2);",
        "                gram[2][0] = gram[0][2];",
        "                gram[1][2] = dot(n1, n2);",
        "                gram[2][1] = gram[1][2];",
        "                gram[2][2] = dot(n2, n2);",
        "            }",
        "            vec3 residual = vec3(",
        "                dot(n0, candidate_velocity),",
        "                active_count >= 2u ? dot(n1, candidate_velocity) : 0.0,",
        "                active_count >= 3u ? dot(n2, candidate_velocity) : 0.0",
        "            ) - limits;",
        "            vec3 multipliers;",
        "            if (!SolveMaximumDepthSystem(",
        "                    gram, residual, active_count, multipliers)) {",
        "                continue;",
        "            }",
        "            if (multipliers.x < -EPSILON",
        "                    || (active_count >= 2u && multipliers.y < -EPSILON)",
        "                    || (active_count >= 3u && multipliers.z < -EPSILON)) {",
        "                continue;",
        "            }",
        "            vec3 velocity = candidate_velocity - multipliers.x * n0;",
        "            if (active_count >= 2u) { velocity -= multipliers.y * n1; }",
        "            if (active_count >= 3u) { velocity -= multipliers.z * n2; }",
        "            bool satisfies_all = true;",
        "            for (uint constraint = 0u;",
        "                    constraint < maximumDepthConstraintCount; ++constraint) {",
        "                if (dot(maximumDepthConstraintNormals[constraint], velocity)",
        "                        > maximumDepthConstraintLimits[constraint] + EPSILON) {",
        "                    satisfies_all = false;",
        "                }",
        "            }",
        "            if (!satisfies_all) { continue; }",
        "            float distance_sq = dot(",
        "                candidate_velocity - velocity, candidate_velocity - velocity);",
        "            if (!found || distance_sq < best_distance_sq) {",
        "                found = true;",
        "                best_distance_sq = distance_sq;",
        "                contained_velocity = velocity;",
        "            }",
        "        }",
        "    }",
        "}",
        "return found;",
    ],
    "ApplySourceMaximumDepth": [
        "if (maximumDepthConstraintOwner != SourceID",
        "        || maximumDepthConstraintCount == 0u) {",
        "    return true;",
        "}",
        "vec3 candidate = GetNextParticleVelocity(SourceID).xyz;",
        "vec3 contained;",
        "if (!ProjectSourceVelocityToContactSet(candidate, contained)) {",
        "    return SetError(ERROR_MAX_DEPTH_CONSTRAINT);",
        "}",
        "float source_mass = GetParticleMass(SourceID);",
        "P[SourceID].parms.yzw +=",
        "    source_mass * (candidate - contained);",
        "P[SourceID].Data.z = length(P[SourceID].parms.yzw);",
        "SetNextParticleVelocity(SourceID, vec4(",
        "    contained, VelocityAngle(contained.x, contained.y)));",
        "maximumDepthConstraintCount = 0u;",
        "return true;",
    ],
    "CalcVelocity": [
        "float dt = ShaderFlags.dt;",
        "if (dt <= 0.0) {",
        "    return SetError(ERROR_INVALID_DT);",
        "}",
        "",
        "float source_mass = GetParticleMass(SourceID);",
        "vec4 start_velocity = GetStartFrameVelocity(SourceID);",
        "vec3 candidate_velocity = start_velocity.xyz + totalForce * dt / source_mass;",
        "SetNextParticleVelocity(SourceID, vec4(",
        "    candidate_velocity,",
        "    VelocityAngle(candidate_velocity.x, candidate_velocity.y)",
        "));",
        "return ApplySourceMaximumDepth(SourceID);",
    ],
    "CalcPosition": [
        "uint position_buffer = uint(ShaderFlags.positionBuffer);",
        "float dt = ShaderFlags.dt;",
        "if (dt <= 0.0) {",
        "    return SetError(ERROR_INVALID_DT);",
        "}",
        "",
        "vec4 position = GetParticlePosition(SourceID);",
        "vec4 velocity = GetNextParticleVelocity(SourceID);",
        "vec4 output_position;",
        "if (position_buffer == 0u) {",
        "    P[SourceID].PosLocB.x = position.x + velocity.x * dt;",
        "    P[SourceID].PosLocB.y = position.y + velocity.y * dt;",
        "    P[SourceID].PosLocB.z = position.z + velocity.z * dt;",
        "    P[SourceID].PosLocA.w = 1.0;",
        "    P[SourceID].PosLocB.w = 0.0;",
        "    output_position = P[SourceID].PosLocB;",
        "} else {",
        "    P[SourceID].PosLocA.x = position.x + velocity.x * dt;",
        "    P[SourceID].PosLocA.y = position.y + velocity.y * dt;",
        "    P[SourceID].PosLocA.z = position.z + velocity.z * dt;",
        "    P[SourceID].PosLocA.w = 0.0;",
        "    P[SourceID].PosLocB.w = 1.0;",
        "    output_position = P[SourceID].PosLocA;",
        "}",
        "",
        "if (ShaderFlags.Boundary == 0.0 && (output_position.x < 1.0 || output_position.y < 1.0)) {",
        "    return SetError(ERROR_PARTICLE_OUT_OF_BOUNDS);",
        "}",
        "return true;",
    ],
    "GetPhysicalWallGhostGeometry": [
        "vec4 position = GetParticlePosition(SourceID);",
        "float radius = P[SourceID].Data.x;",
        "float offset = WallContactOffsetDistance(radius);",
        "vec3 ghost = vec3(0.0);",
        "vec3 normal = vec3(0.0);",
        "",
        "if (wall_flag == 1u) {",
        "    ghost = vec3(BOUNDARY_XMIN - radius + offset, position.y, position.z);",
        "    normal = vec3(-1.0, 0.0, 0.0);",
        "} else if (wall_flag == 2u) {",
        "    ghost = vec3(BOUNDARY_XMAX + radius - offset, position.y, position.z);",
        "    normal = vec3(1.0, 0.0, 0.0);",
        "} else if (wall_flag == 3u) {",
        "    ghost = vec3(position.x, BOUNDARY_YMIN - radius + offset, position.z);",
        "    normal = vec3(0.0, -1.0, 0.0);",
        "} else if (wall_flag == 4u) {",
        "    ghost = vec3(position.x, BOUNDARY_YMAX + radius - offset, position.z);",
        "    normal = vec3(0.0, 1.0, 0.0);",
        "} else {",
        "    return WallPhysicalGhostGeometry(vec3(0.0), 0.0, 0.0, false);",
        "}",
        "",
        "vec3 delta = ghost - position.xyz;",
        "float center_distance = length(delta);",
        "if (center_distance >= 2.0 * radius) {",
        "    return WallPhysicalGhostGeometry(normal, 0.0, center_distance, false);",
        "}",
        "float overlap_area = particle_overlap_area(radius, radius, center_distance);",
        "return WallPhysicalGhostGeometry(normal, overlap_area, center_distance, true);",
    ],
    "GetWallGhostGeometry": [
        "WallPhysicalGhostGeometry physical =",
        "    GetPhysicalWallGhostGeometry(SourceID, wall_flag);",
        "if (!physical.valid) {",
        "    return WallGhostGeometry(",
        "        physical.normal,",
        "        0.0,",
        "        physical.centerDistance,",
        "        0.0,",
        "        0.0,",
        "        0.0,",
        "        0.0,",
        "        false",
        "    );",
        "}",
        "",
        "float radius = P[SourceID].Data.x;",
        "float physical_limit = 2.0 * radius;",
        "float effective_radius = radius;",
        "",
        "// Step 7 ordinary-wall fallback: starting-wall effective radius",
        "// is added later through StartingContactState buffer logic.",
        "if (physical.centerDistance >= 2.0 * effective_radius) {",
        "    return WallGhostGeometry(",
        "        physical.normal,",
        "        0.0,",
        "        physical.centerDistance,",
        "        effective_radius,",
        "        physical_limit,",
        "        0.0,",
        "        0.0,",
        "        false",
        "    );",
        "}",
        "float overlap_area = particle_overlap_area(",
        "    effective_radius,",
        "    effective_radius,",
        "    physical.centerDistance",
        ");",
        "return WallGhostGeometry(",
        "    physical.normal,",
        "    overlap_area,",
        "    physical.centerDistance,",
        "    effective_radius,",
        "    physical_limit,",
        "    0.0,",
        "    0.0,",
        "    true",
        ");",
    ],
    "RegisterMaximumDepthConstraint": [
        "if (maximumDepthConstraintOwner != SourceID) {",
        "    maximumDepthConstraintOwner = SourceID;",
        "    maximumDepthConstraintCount = 0u;",
        "}",
        "float maximum_depth = MAXIMUM_PENETRATION_FRACTION * source_radius;",
        "if (penetration_depth < maximum_depth - EPSILON) {",
        "    return true;",
        "}",
        "if (maximumDepthConstraintCount >= MAX_SOURCE_DEPTH_CONSTRAINTS) {",
        "    return SetError(ERROR_MAX_DEPTH_CONSTRAINT);",
        "}",
        "maximumDepthConstraintNormals[maximumDepthConstraintCount] = normal;",
        "maximumDepthConstraintLimits[maximumDepthConstraintCount] = 0.0;",
        "maximumDepthConstraintCount += 1u;",
        "return true;",
    ],
    "SolveMaximumDepthSystem": [
        "solution = vec3(0.0);",
        "if (size == 1u) {",
        "    if (abs(matrix[0][0]) <= EPSILON) { return false; }",
        "    solution.x = values.x / matrix[0][0];",
        "    return true;",
        "}",
        "if (size == 2u) {",
        "    float det = matrix[0][0] * matrix[1][1]",
        "        - matrix[1][0] * matrix[0][1];",
        "    if (abs(det) <= EPSILON) { return false; }",
        "    solution.x = (values.x * matrix[1][1]",
        "        - matrix[1][0] * values.y) / det;",
        "    solution.y = (matrix[0][0] * values.y",
        "        - values.x * matrix[0][1]) / det;",
        "    return true;",
        "}",
        "if (size == 3u) {",
        "    float det = determinant(matrix);",
        "    if (abs(det) <= EPSILON) { return false; }",
        "    mat3 mx = matrix;",
        "    mat3 my = matrix;",
        "    mat3 mz = matrix;",
        "    mx[0] = values;",
        "    my[1] = values;",
        "    mz[2] = values;",
        "    solution = vec3(",
        "        determinant(mx), determinant(my), determinant(mz)) / det;",
        "    return true;",
        "}",
        "return false;",
    ],
    "StartReservoir": [
        "float state_flag = P[SourceID].Data.w;",
        "if (state_flag < 0.0) {",
        "    return false;",
        "}",
        "if (state_flag == 0.0) {",
        "    return true;",
        "}",
        "if (ShaderFlags.frameNum < state_flag) {",
        "    return false;",
        "}",
        "",
        "uint position_buffer = uint(ShaderFlags.positionBuffer);",
        "vec4 current_position = particle_position(SourceID, position_buffer);",
        "float radius = P[SourceID].Data.x;",
        "",
        "#if defined(PERIODIC_DIRECTION) && PERIODIC_DIRECTION == vertical",
        "float inlet_y = BOUNDARY_YMIN;",
        "#ifdef INLET_Y",
        "inlet_y = INLET_Y;",
        "#endif",
        "vec3 start_position = vec3(",
        "    current_position.x,",
        "    inlet_y + 2.2 * radius,",
        "    current_position.z",
        ");",
        "#else",
        "float inlet_x = BOUNDARY_XMIN;",
        "#ifdef INLET_X",
        "inlet_x = INLET_X;",
        "#endif",
        "",
        "vec3 start_position = vec3(",
        "    inlet_x + 2.2 * radius,",
        "    current_position.y,",
        "    current_position.z",
        ");",
        "#endif",
        "P[SourceID].PosLocA.xyz = start_position;",
        "P[SourceID].PosLocB.xyz = start_position;",
        "P[SourceID].PosLocA.w = position_buffer == 0u ? 0.0 : 1.0;",
        "P[SourceID].PosLocB.w = position_buffer == 0u ? 1.0 : 0.0;",
        "P[SourceID].Data.w = 0.0;",
        "return true;",
    ],
    "RetireParticlePastXMax": [
        "uint next_position_buffer = 1u - uint(ShaderFlags.positionBuffer);",
        "vec4 next_position = particle_position(SourceID, next_position_buffer);",
        "#if defined(PERIODIC_DIRECTION) && PERIODIC_DIRECTION == vertical",
        "float outlet_y = BOUNDARY_YMAX;",
        "#ifdef OUTLET_Y",
        "outlet_y = OUTLET_Y;",
        "#endif",
        "if (next_position.y > outlet_y) {",
        "    float inlet_y = BOUNDARY_YMIN;",
        "#ifdef INLET_Y",
        "    inlet_y = INLET_Y;",
        "#endif",
        "    vec3 reservoir_position = vec3(",
        "        next_position.x,",
        "        inlet_y,",
        "        next_position.z",
        "    );",
        "#else",
        "float outlet_x = BOUNDARY_XMAX;",
        "#ifdef OUTLET_X",
        "outlet_x = OUTLET_X;",
        "#endif",
        "if (next_position.x > outlet_x) {",
        "    float inlet_x = BOUNDARY_XMIN;",
        "#ifdef INLET_X",
        "    inlet_x = INLET_X;",
        "#endif",
        "    vec3 reservoir_position = vec3(",
        "        inlet_x,",
        "        next_position.y,",
        "        next_position.z",
        "    );",
        "#endif",
        "    P[SourceID].PosLocA.xyz = reservoir_position;",
        "    P[SourceID].PosLocB.xyz = reservoir_position;",
        "    P[SourceID].PosLocA.w = next_position_buffer == 0u ? 0.0 : 1.0;",
        "    P[SourceID].PosLocB.w = next_position_buffer == 0u ? 1.0 : 0.0;",
        "    P[SourceID].VelRad.xyz = vec3(0.0);",
        "    P[SourceID].VelRad.w = 0.0;",
        "    P[SourceID].Data.w = -1.0;",
        "    return false;",
        "}",
        "return true;",
    ],
    "RetireParticleAtCellGuard": [
        "uint next_position_buffer = 1u - uint(ShaderFlags.positionBuffer);",
        "vec4 next_position = particle_position(SourceID, next_position_buffer);",
        "float radius = P[SourceID].Data.x;",
        "#if defined(PERIODIC_DIRECTION) && PERIODIC_DIRECTION == vertical",
        "float inlet_guard_y = BOUNDARY_YMIN + 2.2 * radius;",
        "#ifdef INLET_Y",
        "inlet_guard_y = INLET_Y + 2.2 * radius;",
        "#endif",
        "if (next_position.y <= inlet_guard_y) {",
        "    return true;",
        "}",
        "#else",
        "float inlet_guard_x = BOUNDARY_XMIN + 2.2 * radius;",
        "#ifdef INLET_X",
        "inlet_guard_x = INLET_X + 2.2 * radius;",
        "#endif",
        "if (next_position.x <= inlet_guard_x) {",
        "    return true;",
        "}",
        "#endif",
        "#if defined(PERIODIC_DIRECTION) && PERIODIC_DIRECTION == vertical",
        "bool outside_cell_guard = (",
        "    next_position.x <= 1.0 ||",
        "    next_position.z <= 1.0 ||",
        "    next_position.x >= float(WIDTH - 2u) ||",
        "    next_position.y >= float(HEIGHT - 2u) ||",
        "    next_position.z >= float(DEPTH - 2u)",
        ");",
        "#else",
        "bool outside_cell_guard = (",
        "    next_position.y <= 1.0 ||",
        "    next_position.z <= 1.0 ||",
        "    next_position.x >= float(WIDTH - 2u) ||",
        "    next_position.y >= float(HEIGHT - 2u) ||",
        "    next_position.z >= float(DEPTH - 2u)",
        ");",
        "#endif",
        "if (outside_cell_guard) {",
        "    P[SourceID].VelRad.xyz = vec3(0.0);",
        "    P[SourceID].VelRad.w = 0.0;",
        "    P[SourceID].Data.w = -1.0;",
        "    return false;",
        "}",
        "return true;",
    ],
    "SetError": [
        "collOut.ErrorNumber = error_code;",
        "return false;",
    ],
}


class ForceDynamicsVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.class_node: ast.ClassDef | None = None
        self.methods: dict[str, ast.FunctionDef] = {}
        self.self_calls: dict[str, set[int]] = {}
        self.method_self_calls: dict[str, dict[str, set[int]]] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.name != "ForceContactDynamics":
            return
        self.class_node = node
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.methods[item.name] = item
                self.method_self_calls[item.name] = collect_self_calls(item)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "self"
        ):
            self.self_calls.setdefault(func.attr, set()).add(node.lineno)
        self.generic_visit(node)


def collect_self_calls(method: ast.FunctionDef) -> dict[str, set[int]]:
    calls: dict[str, set[int]] = {}
    for node in ast.walk(method):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "self"
        ):
            calls.setdefault(func.attr, set()).add(node.lineno)
    return calls


def parse_source(source_path: Path) -> ForceDynamicsVisitor:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    visitor = ForceDynamicsVisitor()
    visitor.visit(tree)
    if visitor.class_node is None:
        raise SystemExit(f"ERROR: ForceContactDynamics not found in {source_path}")
    return visitor


def format_lines(lines: set[int]) -> str:
    return ", ".join(str(line) for line in sorted(lines))


def validate_export_surface(visitor: ForceDynamicsVisitor) -> tuple[bool, list[str]]:
    defined_methods = set(visitor.methods)
    generated_methods = set(GENERATED_GLSL_METHODS)
    wrapper_methods = set(PYTHON_WRAPPER_METHODS)
    missing_generated_methods = generated_methods - defined_methods
    stale_generated_methods = generated_methods & wrapper_methods
    missing_signatures = generated_methods - set(GLSL_SIGNATURES)
    classified_methods = {
        method_name
        for method_names in TRANSLATION_STATUS.values()
        for method_name in method_names
    }
    missing_status = generated_methods - classified_methods
    stale_status = classified_methods - generated_methods

    generated_calls: dict[str, set[int]] = {}
    dependency_checked_methods = [
        method_name
        for method_name in GENERATED_GLSL_METHODS
        if method_name not in GLSL_BODY_TEMPLATES
        and method_name not in TRANSLATION_STATUS["defer"]
        and method_name not in TRANSLATION_STATUS["needs_buffer"]
    ]
    for method_name in dependency_checked_methods:
        for call_name, lines in visitor.method_self_calls.get(method_name, {}).items():
            generated_calls.setdefault(call_name, set()).update(lines)
    generated_external_calls = set(generated_calls) - generated_methods

    unexpected_generated_calls = (
        generated_external_calls - set(KNOWN_TRANSLATION_PRIMITIVES)
    )

    errors = []
    if missing_generated_methods:
        errors.append(
            "generated GLSL method list contains missing methods: "
            + ", ".join(sorted(missing_generated_methods))
        )
    if stale_generated_methods:
        errors.append(
            "methods cannot be both generated and wrapper-only: "
            + ", ".join(sorted(stale_generated_methods))
        )
    if missing_signatures:
        errors.append(
            "generated GLSL methods have no stub signature: "
            + ", ".join(sorted(missing_signatures))
        )
    if missing_status:
        errors.append(
            "generated GLSL methods have no translation status: "
            + ", ".join(sorted(missing_status))
        )
    if stale_status:
        errors.append(
            "translation status contains non-generated methods: "
            + ", ".join(sorted(stale_status))
        )
    if unexpected_generated_calls:
        errors.append(
            "generated GLSL methods have unexpected dependencies: "
            + ", ".join(sorted(unexpected_generated_calls))
        )
    return not errors, errors


def glsl_return_type(signature: str) -> str:
    return signature.split(" ", 1)[0]


def render_method_bodies(
    source_path: Path,
    visitor: ForceDynamicsVisitor,
    method_names: list[str],
) -> list[str]:
    lines = []
    for method_name in method_names:
        method = visitor.methods[method_name]
        signature = GLSL_SIGNATURES[method_name]
        return_type = glsl_return_type(signature)
        lines.append(f"// Python source: {source_path.name}:{method.lineno}")
        lines.append(signature)
        lines.append("{")
        body_template = GLSL_BODY_TEMPLATES.get(method_name)
        if body_template is not None:
            for body_line in body_template:
                lines.append(f"    {body_line}" if body_line else "")
        else:
            lines.append(f"    // TODO: generate body for {method_name}.")
            default_return = GLSL_DEFAULT_RETURNS.get(return_type)
            if default_return is not None:
                lines.append(f"    return {default_return};")
        lines.append("}")
        lines.append("")
    return lines


def render_helper_bodies(method_names: list[str]) -> list[str]:
    lines = []
    for method_name in method_names:
        signature = GLSL_SIGNATURES[method_name]
        lines.append(f"// Custom GLSL helper: {method_name}")
        lines.append(signature)
        lines.append("{")
        for body_line in GLSL_BODY_TEMPLATES[method_name]:
            lines.append(f"    {body_line}" if body_line else "")
        lines.append("}")
        lines.append("")
    return lines


def render_core_glsl_file(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    lines = [
        "#ifndef FORCE_DYNAMICS_GLSL",
        "#define FORCE_DYNAMICS_GLSL",
        "",
        "// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.",
        "// Core reusable force dynamics. Boundary-particle wall helpers are split",
        "// into ForceDynamicsBoundaryParticle.glsl and ForceDynamicsCDNozzle.glsl.",
        "// Do not hand edit generated dynamics content.",
        "",
        "const float EPSILON = 1.0e-12;",
        "const float FORCE_DYNAMICS_PI = 3.1415926535897932384626433832795;",
        "const uint ERROR_NONE = 0u;",
        "const uint ERROR_INVALID_SOURCE_ID = 1u;",
        "const uint ERROR_INVALID_TARGET_ID = 2u;",
        "const uint ERROR_INVALID_DT = 3u;",
        "const uint ERROR_CONTACT_LIST_MISSING = 4u;",
        "const uint ERROR_PARTICLE_OUT_OF_BOUNDS = 5u;",
        "const uint ERROR_PARTICLE_TUNNELING = 6u;",
        "const uint ERROR_MISSING_COLLISION_STIFFNESS_Q = 7u;",
        "const uint ERROR_WALL_TUNNELING = 8u;",
        "const uint ERROR_MAX_DEPTH_CONSTRAINT = 9u;",
        "const uint ERROR_PENETRATION_STEP_TOO_LARGE = 10u;",
        "const float MAXIMUM_PENETRATION_FRACTION = 0.5;",
        "const uint CONTACT_INACTIVE = 0u;",
        "const uint CONTACT_PARTICLE = 1u;",
        "const uint CONTACT_WALL = 2u;",
        "#ifndef horizontal_wall",
        "#define horizontal_wall 1",
        "#endif",
        "#ifndef vertical_wall",
        "#define vertical_wall 2",
        "#endif",
        "#ifndef cd_nozzle_wall",
        "#define cd_nozzle_wall 3",
        "#endif",
        "#ifndef horizontal",
        "#define horizontal 1",
        "#endif",
        "#ifndef vertical",
        "#define vertical 2",
        "#endif",
        "#ifndef wall_guard",
        "#define wall_guard 1",
        "#endif",
        "#ifndef cell_guard",
        "#define cell_guard 2",
        "#endif",
        "#ifndef area",
        "#define area 1",
        "#endif",
        "#ifndef depth",
        "#define depth 2",
        "#endif",
        "",
    ]

    for struct_name, fields in GLSL_RESULT_STRUCTS:
        lines.append(f"struct {struct_name} {{")
        for field in fields:
            lines.append(f"    {field}")
        lines.append("};")
        lines.append("")

    lines.extend(
        [
            "#ifndef MAX_SOURCE_DEPTH_CONSTRAINTS",
            "#define MAX_SOURCE_DEPTH_CONSTRAINTS 16",
            "#endif",
            "uint maximumDepthConstraintOwner = 0xffffffffu;",
            "uint maximumDepthConstraintCount = 0u;",
            "vec3 maximumDepthConstraintNormals[MAX_SOURCE_DEPTH_CONSTRAINTS];",
            "float maximumDepthConstraintLimits[MAX_SOURCE_DEPTH_CONSTRAINTS];",
            "",
        ]
    )

    lines.append("// Forward declarations for generated core methods.")
    for method_name in CORE_GLSL_METHODS:
        lines.append(f"{GLSL_SIGNATURES[method_name]};")
    for method_name in CUSTOM_GLSL_HELPERS:
        lines.append(f"{GLSL_SIGNATURES[method_name]};")
    lines.append("")

    lines.extend(render_method_bodies(source_path, visitor, CORE_GLSL_METHODS))
    lines.extend(render_helper_bodies(CUSTOM_GLSL_HELPERS))

    lines.append("#endif")
    lines.append("")
    return "\n".join(lines)


def render_boundary_particle_glsl_file(
    source_path: Path, visitor: ForceDynamicsVisitor
) -> str:
    lines = [
        "#ifndef FORCE_DYNAMICS_BOUNDARY_PARTICLE_GLSL",
        "#define FORCE_DYNAMICS_BOUNDARY_PARTICLE_GLSL",
        "",
        "// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.",
        "// Generic boundary-particle wall helpers. Requires ForceDynamics.glsl.",
        "// Do not hand edit generated dynamics content.",
        "",
        "// Forward declarations for boundary-particle methods.",
    ]
    for method_name in BOUNDARY_PARTICLE_GLSL_METHODS:
        lines.append(f"{GLSL_SIGNATURES[method_name]};")
    lines.append(GLSL_SIGNATURES["EvaluateCDNozzleWallSegment"] + ";")
    lines.append(GLSL_SIGNATURES["EvaluateWallSegment"] + ";")
    lines.append("")
    lines.extend(
        render_method_bodies(source_path, visitor, BOUNDARY_PARTICLE_GLSL_METHODS)
    )
    lines.extend(
        render_method_bodies(source_path, visitor, ["EvaluateWallSegment"])
    )
    lines.append("")
    lines.append("#endif")
    lines.append("")
    return "\n".join(lines)


def render_cd_nozzle_glsl_file(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    lines = [
        "#ifndef FORCE_DYNAMICS_CD_NOZZLE_GLSL",
        "#define FORCE_DYNAMICS_CD_NOZZLE_GLSL",
        "",
        "// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.",
        "// CD nozzle boundary-particle wall helpers. Requires ForceDynamics.glsl",
        "// and ForceDynamicsBoundaryParticle.glsl.",
        "// Do not hand edit generated dynamics content.",
        "",
        "// Forward declarations for CD nozzle methods.",
    ]
    for method_name in CD_NOZZLE_GLSL_METHODS:
        lines.append(f"{GLSL_SIGNATURES[method_name]};")
    lines.append("")
    lines.extend(render_method_bodies(source_path, visitor, CD_NOZZLE_GLSL_METHODS))
    lines.extend(["", "#endif", ""])
    return "\n".join(lines)


def write_stub_file(output_path: Path, source_path: Path, visitor: ForceDynamicsVisitor) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_core_glsl_file(source_path, visitor), encoding="utf-8")
    DEFAULT_BOUNDARY_OUTPUT.write_text(
        render_boundary_particle_glsl_file(source_path, visitor),
        encoding="utf-8",
    )
    DEFAULT_CD_NOZZLE_OUTPUT.write_text(
        render_cd_nozzle_glsl_file(source_path, visitor),
        encoding="utf-8",
    )

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report the ForceDynamics.py surface available for GLSL export."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Python dynamics source file. Default: {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Generated GLSL output file. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--write-stubs",
        action="store_true",
        help="Write a stub ForceDynamics.glsl artifact after the report gate passes.",
    )
    args = parser.parse_args()

    source_path = args.source.resolve()
    visitor = parse_source(source_path)

    defined_methods = set(visitor.methods)
    generated_methods = set(GENERATED_GLSL_METHODS)
    wrapper_methods = set(PYTHON_WRAPPER_METHODS)
    called_methods = set(visitor.self_calls)
    external_calls = called_methods - defined_methods
    missing_generated_methods = generated_methods - defined_methods
    stale_generated_methods = generated_methods & wrapper_methods
    missing_signatures = generated_methods - set(GLSL_SIGNATURES)
    classified_methods = {
        method_name
        for method_names in TRANSLATION_STATUS.values()
        for method_name in method_names
    }
    missing_status = generated_methods - classified_methods
    stale_status = classified_methods - generated_methods

    generated_calls: dict[str, set[int]] = {}
    dependency_checked_methods = [
        method_name
        for method_name in GENERATED_GLSL_METHODS
        if method_name not in GLSL_BODY_TEMPLATES
        and method_name not in TRANSLATION_STATUS["defer"]
        and method_name not in TRANSLATION_STATUS["needs_buffer"]
    ]
    for method_name in dependency_checked_methods:
        for call_name, lines in visitor.method_self_calls.get(method_name, {}).items():
            generated_calls.setdefault(call_name, set()).update(lines)
    generated_external_calls = set(generated_calls) - generated_methods

    allowed_generated_external_calls = set(KNOWN_TRANSLATION_PRIMITIVES)
    unexpected_generated_calls = (
        generated_external_calls - allowed_generated_external_calls
    )

    print("ForceDynamics GLSL export report")
    print(f"Source: {source_path}")
    print()

    print("Generated GLSL methods:")
    for name in GENERATED_GLSL_METHODS:
        method = visitor.methods.get(name)
        if method is None:
            print(f"  MISSING  {name}")
        else:
            print(f"  {method.lineno:4d}  {name}")
    print()

    print("Python wrapper or harness methods:")
    for name in PYTHON_WRAPPER_METHODS:
        method = visitor.methods.get(name)
        if method is None:
            print(f"  MISSING  {name}")
        else:
            print(f"  {method.lineno:4d}  {name}")
    print()

    print("Other ForceDynamics.py methods:")
    categorized_methods = generated_methods | wrapper_methods
    other_methods = {
        name: method
        for name, method in visitor.methods.items()
        if name not in categorized_methods
    }
    if not other_methods:
        print("  none")
    for name, method in sorted(other_methods.items(), key=lambda item: item[1].lineno):
        print(f"  {method.lineno:4d}  {name}")
    print()

    print("Known translation primitives:")
    if not KNOWN_TRANSLATION_PRIMITIVES:
        print("  none")
    for name, description in sorted(KNOWN_TRANSLATION_PRIMITIVES.items()):
        lines = visitor.self_calls.get(name, set())
        line_text = f" lines {format_lines(lines)}" if lines else ""
        print(f"  {name}{line_text}: {description}")
    print()

    print("Translation status:")
    for status, method_names in TRANSLATION_STATUS.items():
        description = TRANSLATION_STATUS_DESCRIPTIONS[status]
        print(f"  {status}: {description}")
        for method_name in method_names:
            method = visitor.methods.get(method_name)
            if method is None:
                print(f"       MISSING  {method_name}")
            else:
                print(f"       {method.lineno:4d}  {method_name}")
    print()

    print("External self-method calls:")
    if not external_calls:
        print("  none")
    for name in sorted(external_calls):
        status = "known" if name in KNOWN_TRANSLATION_PRIMITIVES else "unexpected"
        print(f"  {name} ({status}) at lines {format_lines(visitor.self_calls[name])}")
    print()

    print("Generated-method external calls:")
    if not generated_external_calls:
        print("  none")
    for name in sorted(generated_external_calls):
        status = "known" if name in KNOWN_TRANSLATION_PRIMITIVES else "unexpected"
        print(f"  {name} ({status}) at lines {format_lines(generated_calls[name])}")
    print()

    if missing_generated_methods:
        print("ERROR: generated GLSL method list contains missing methods.")
        return 1

    if stale_generated_methods:
        print("ERROR: methods cannot be both generated and wrapper-only.")
        return 1

    if missing_signatures:
        print("ERROR: generated GLSL methods have no stub signature.")
        return 1

    if missing_status:
        print("ERROR: generated GLSL methods have no translation status.")
        return 1

    if stale_status:
        print("ERROR: translation status contains non-generated methods.")
        return 1

    if unexpected_generated_calls:
        print("ERROR: generated GLSL methods have unexpected dependencies.")
        return 1

    print("OK: generated GLSL method surface is self-contained.")
    if args.write_stubs:
        output_path = args.output.resolve()
        write_stub_file(output_path, source_path, visitor)
        print(f"Wrote stub GLSL: {output_path}")
        print(f"Wrote boundary-particle GLSL: {DEFAULT_BOUNDARY_OUTPUT}")
        print(f"Wrote CD nozzle GLSL: {DEFAULT_CD_NOZZLE_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
