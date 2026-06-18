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

KNOWN_TRANSLATION_PRIMITIVES = {
    "create_vec4": "Python vector factory; maps to vec4(...) in GLSL.",
}

GENERATED_GLSL_METHODS = [
    "VelocityAngle",
    "particle_position",
    "particle_overlap_area",
    "ProcessParticleCollision",
    "ProcessWallCollision",
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
    "CalcVelocity",
    "GetParticleMass",
    "CalcPosition",
    "SetError",
]

PYTHON_WRAPPER_METHODS = [
    "isParticleContact",
    "DetectContacts",
    "NaiveContactDetermination",
    "AddContactTargetID",
    "BuildWallContactLists",
    "CalculateVelocities",
    "CalculatePositions",
]

GLSL_SIGNATURES = {
    "VelocityAngle": "float VelocityAngle(float vx, float vy)",
    "particle_position": "vec4 particle_position(uint ParticleID, uint positionBuffer)",
    "particle_overlap_area": (
        "float particle_overlap_area(float source_radius, "
        "float target_radius, float center_distance)"
    ),
    "ProcessParticleCollision": (
        "bool ProcessParticleCollision(uint TargetID, uint SourceID, "
        "inout vec3 totalForce)"
    ),
    "ProcessWallCollision": (
        "bool ProcessWallCollision(uint SourceID, uint wall, inout vec3 totalForce)"
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
    "CalcVelocity": "bool CalcVelocity(uint SourceID, vec3 totalForce)",
    "GetParticleMass": "float GetParticleMass(uint ParticleID)",
    "CalcPosition": "bool CalcPosition(uint SourceID)",
    "SetError": "bool SetError(uint error_code)",
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
        "ContactForceInput",
        [
            "uint targetID;",
            "uint contactType;",
            "vec3 normal;",
            "float overlapArea;",
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
        "CalcVelocity",
        "CalcPosition",
        "AccumulateContactForce",
        "ProcessParticleCollision",
        "ProcessWallCollision",
        "SetError",
    ],
    "needs_struct": [
        "GetParticleGeometry",
        "GetParticleEffectiveContactGeometry",
        "GetParticlePotentialGeometry",
        "GetPhysicalWallGhostGeometry",
        "GetWallGhostGeometry",
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
    "CalcVelocity",
    "CalcPosition",
    "GetPhysicalWallGhostGeometry",
    "GetWallGhostGeometry",
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
        "    return PI * min_radius * min_radius;",
        "}",
        "if (center_distance >= source_radius + target_radius) {",
        "    return 0.0;",
        "}",
        "if (center_distance <= abs(source_radius - target_radius)) {",
        "    float min_radius = min(source_radius, target_radius);",
        "    return PI * min_radius * min_radius;",
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
    "ProcessParticleCollision": [
        "ParticleGeometry geometry = GetParticleGeometry(SourceID, TargetID);",
        "ContactForceInput contact = ContactForceInput(",
        "    TargetID,",
        "    CONTACT_PARTICLE,",
        "    geometry.normal,",
        "    geometry.overlapArea,",
        "    geometry.valid",
        ");",
        "return AccumulateContactForce(SourceID, contact, totalForce);",
    ],
    "ProcessWallCollision": [
        "WallGhostGeometry geometry = GetWallGhostGeometry(SourceID, wall);",
        "ContactForceInput contact = ContactForceInput(",
        "    wall,",
        "    CONTACT_WALL,",
        "    geometry.normal,",
        "    geometry.overlapArea,",
        "    geometry.valid",
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
        "return P[ParticleID].VelRad;",
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
        "float force_magnitude = stiffness * max(0.0, contact.overlapArea);",
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
    "CalcVelocity": [
        "float dt = ShaderFlags.dt;",
        "if (dt <= 0.0) {",
        "    return SetError(ERROR_INVALID_DT);",
        "}",
        "",
        "float source_mass = GetParticleMass(SourceID);",
        "vec4 start_velocity = GetStartFrameVelocity(SourceID);",
        "P[SourceID].VelRad.x = start_velocity.x + totalForce.x * dt / source_mass;",
        "P[SourceID].VelRad.y = start_velocity.y + totalForce.y * dt / source_mass;",
        "P[SourceID].VelRad.z = start_velocity.z + totalForce.z * dt / source_mass;",
        "P[SourceID].VelRad.w = VelocityAngle(P[SourceID].VelRad.x, P[SourceID].VelRad.y);",
        "return true;",
    ],
    "CalcPosition": [
        "uint position_buffer = uint(ShaderFlags.positionBuffer);",
        "float dt = ShaderFlags.dt;",
        "if (dt <= 0.0) {",
        "    return SetError(ERROR_INVALID_DT);",
        "}",
        "",
        "vec4 position = GetParticlePosition(SourceID);",
        "vec4 velocity = P[SourceID].VelRad;",
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
    "SetError": [
        "collIn.ErrorReturn = error_code;",
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
    for method_name in GENERATED_GLSL_METHODS:
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


def render_stub_file(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    lines = [
        "#ifndef FORCE_DYNAMICS_GLSL",
        "#define FORCE_DYNAMICS_GLSL",
        "",
        "// Generated from base/ForceDynamics.py by tools/ExportForceDynamicsGLSL.py.",
        "// Some direct read-only/math bodies are generated from explicit templates.",
        "// Methods without templates remain non-functional stubs.",
        "// Do not hand edit generated dynamics content.",
        "",
        "const float EPSILON = 1.0e-12;",
        "const float PI = 3.1415926535897932384626433832795;",
        "",
    ]

    for struct_name, fields in GLSL_RESULT_STRUCTS:
        lines.append(f"struct {struct_name} {{")
        for field in fields:
            lines.append(f"    {field}")
        lines.append("};")
        lines.append("")

    for method_name in GENERATED_GLSL_METHODS:
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

    lines.append("#endif")
    lines.append("")
    return "\n".join(lines)


def write_stub_file(output_path: Path, source_path: Path, visitor: ForceDynamicsVisitor) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_stub_file(source_path, visitor), encoding="utf-8")


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
    for method_name in GENERATED_GLSL_METHODS:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
