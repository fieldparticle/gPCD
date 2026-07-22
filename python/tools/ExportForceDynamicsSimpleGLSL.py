"""Export the clean simple ForceDynamics GLSL family.

This exporter intentionally does not share the legacy exporter surface.  It
targets the GenericGenData/TestPythonBoundarySpheres model:

- active mobile particles
- boundary particles as locality markers
- function-wall segments
- no reservoir lifecycle
- optional analytic piston for packed reservoir tests
- no CD-nozzle/horizontal/vertical evaluator dispatch
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PYTHON_ROOT / "base" / "ForceDynamics.py"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "vulkan" / "sim" / "common"
DEFAULT_COMPUTE_OUTPUT = (
    REPO_ROOT
    / "vulkan"
    / "sim"
    / "TestPythonBoundarySpheres"
    / "TestPythonBoundarySpheresP.comp"
)

SIMPLE_CORE_METHODS = [
    "VelocityAngle",
    "particle_position",
    "particle_overlap_area",
    "ParticlePenetrationDepth",
    "GetParticleGeometry",
    "GetPhysicalParticleContact",
    "ProcessParticleCollision",
    "GetParticlePosition",
    "GetParticleVelocity",
    "GetStartFrameVelocity",
    "IsNullParticle",
    "IsBoundaryParticle",
    "IsParticleDead",
    "IsParticlePendingBirth",
    "IsParticleBorn",
    "IsParticleActiveForLifecycle",
    "IsMobileParticleActiveForDynamics",
    "AppendContactSlot",
    "GetContactSlots",
    "AccumulateContactForce",
    "GetPairStiffness",
    "GetContactStiffness",
    "WallContactOffsetDistance",
    "AppendWallContactSlot",
    "CheckPenetrationStepResolution",
    "ProjectSourceVelocityToContactSet",
    "ApplySourceMaximumDepth",
    "CalcVelocity",
    "GetParticleMass",
    "CalcPosition",
    "SetError",
]

SIMPLE_BOUNDARY_METHODS = [
    "BoundaryMarkerApplies",
    "ProcessFunctionWallCollision",
    "InitializeFunctionWallContactState",
]

SIMPLE_FUNCTION_WALL_METHODS = [
    "EvaluateFunctionWallSegment",
]

SIMPLE_RECTANGLE_WALL_METHODS = [
    "EvaluateRectangleWallSegment",
    "EvaluateConfiguredWallContacts",
]

SIMPLE_LIGHTING_BALL_METHODS = [
    "LightingBallConfig",
    "EvaluateLightingBallContact",
    "ProcessLightingBallCollision",
]

SIMPLE_PISTON_METHODS = [
    "PistonEnabled",
    "GetPistonPosition",
    "GetPistonVelocity",
    "EvaluatePistonWall",
    "ProcessPistonCollision",
]

RETIRED_METHODS = {
    "ProcessWallCollision",
    "InitializeWallContactState",
    "BoundaryParticleWallFlag",
    "BoundaryParticleVerticalWallFlag",
    "BoundaryParticleCDNozzleWallFlag",
    "CDNozzleRadius",
    "CDNozzleRadiusSlope",
    "EvaluateWallSegment",
    "EvaluateHorizontalWallSegment",
    "EvaluateVerticalWallSegment",
    "EvaluateCDNozzleWallSegment",
    "EvaluateLinearWallSegment",
    "StartingParticleKey",
    "StartingWallKey",
    "InitializeStartingContactState",
    "GetParticleEffectiveContactGeometry",
    "GetParticlePotentialGeometry",
    "isParticleContact",
}


class ForceDynamicsVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.methods: dict[str, ast.FunctionDef] = {}
        self.method_self_calls: dict[str, set[str]] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.name != "ForceContactDynamics":
            return
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.methods[item.name] = item
                self.method_self_calls[item.name] = collect_self_calls(item)


def collect_self_calls(method: ast.FunctionDef) -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(method):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "self"
        ):
            calls.add(func.attr)
    return calls


def parse_source(source_path: Path) -> ForceDynamicsVisitor:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    visitor = ForceDynamicsVisitor()
    visitor.visit(tree)
    if not visitor.methods:
        raise SystemExit(f"ERROR: ForceContactDynamics not found in {source_path}")
    return visitor


def validate_surface(visitor: ForceDynamicsVisitor) -> list[str]:
    exported = set(
        SIMPLE_CORE_METHODS
        + SIMPLE_BOUNDARY_METHODS
        + SIMPLE_FUNCTION_WALL_METHODS
        + SIMPLE_RECTANGLE_WALL_METHODS
        + SIMPLE_LIGHTING_BALL_METHODS
        + SIMPLE_PISTON_METHODS
    )
    errors: list[str] = []
    missing = exported - set(visitor.methods)
    if missing:
        errors.append("missing simple export methods: " + ", ".join(sorted(missing)))

    stale = exported & RETIRED_METHODS
    if stale:
        errors.append("retired methods are in simple export set: " + ", ".join(sorted(stale)))

    for method_name in sorted(exported):
        calls = visitor.method_self_calls.get(method_name, set())
        retired_calls = calls & RETIRED_METHODS
        if retired_calls:
            errors.append(
                f"{method_name} calls retired method(s): "
                + ", ".join(sorted(retired_calls))
            )
    return errors


def method_line(visitor: ForceDynamicsVisitor, method_name: str) -> str:
    method = visitor.methods.get(method_name)
    if method is None:
        return "unknown"
    return str(method.lineno)


def render_core(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    line = lambda name: method_line(visitor, name)
    return f"""#ifndef FORCE_DYNAMICS_SIMPLE_GLSL
#define FORCE_DYNAMICS_SIMPLE_GLSL

// Generated from {source_path.as_posix()} by tools/ExportForceDynamicsSimpleGLSL.py.
// Clean simple dynamics target for GenericGenData/TestPythonBoundarySpheres.
// Do not hand edit generated dynamics content.

const float EPSILON = 1.0e-12;
const float MAXIMUM_DEPTH_SOLVER_EPSILON = 1.0e-6;
const float FORCE_DYNAMICS_PI = 3.1415926535897932384626433832795;
const float TARGET_PENETRATION_FRACTION = 0.5;
const float HARD_PENETRATION_FRACTION = 0.75;
#ifndef FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_GAIN
#define FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_GAIN 8.0
#endif
#ifndef FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_POWER
#define FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_POWER 2.0
#endif
const uint CONTACT_PARTICLE = 1u;
const uint CONTACT_WALL = 2u;
const uint CONTACT_ACTIVE_THIS_FRAME = 1u;
const uint ERROR_NONE = 0u;
const uint ERROR_INVALID_DT = 3u;
const uint ERROR_CONTACT_LIST_MISSING = 4u;
const uint ERROR_PARTICLE_OUT_OF_BOUNDS = 5u;
const uint ERROR_PARTICLE_TUNNELING = 6u;
const uint ERROR_WALL_TUNNELING = 8u;
const uint ERROR_MAX_DEPTH_CONSTRAINT = 9u;
const uint ERROR_PENETRATION_STEP_TOO_LARGE = 10u;

struct ParticleGeometry
{{
    vec3 normal;
    float overlapArea;
    float centerDistance;
    float sourceRadius;
    float targetRadius;
    bool valid;
}};

struct BoundaryWallSegment
{{
    vec3 normal;
    float overlapArea;
    float centerDistance;
    uint wallFlag;
    bool valid;
}};

struct ContactForceInput
{{
    uint targetID;
    uint contactType;
    vec3 normal;
    float overlapArea;
    float penetrationDepth;
    vec3 targetVelocity;
    bool valid;
}};

#ifndef MAX_SOURCE_DEPTH_CONSTRAINTS
#define MAX_SOURCE_DEPTH_CONSTRAINTS 16
#endif
uint maximumDepthConstraintOwner = 0xffffffffu;
uint maximumDepthConstraintCount = 0u;
vec3 maximumDepthConstraintNormals[MAX_SOURCE_DEPTH_CONSTRAINTS];
float maximumDepthConstraintLimits[MAX_SOURCE_DEPTH_CONSTRAINTS];

// Python source: ForceDynamics.py:{line("VelocityAngle")}
float VelocityAngle(float vx, float vy)
{{
    return (vx != 0.0 || vy != 0.0) ? atan(vy, vx) : 0.0;
}}

// Python source: ForceDynamics.py:{line("particle_position")}
vec4 particle_position(uint ParticleID, uint positionBuffer)
{{
    return (positionBuffer == 0u) ? P[ParticleID].PosLocA : P[ParticleID].PosLocB;
}}

// Python source: ForceDynamics.py:{line("particle_overlap_area")}
float particle_overlap_area(float sourceRadius, float targetRadius, float centerDistance)
{{
    if (centerDistance <= 0.0) {{
        float minRadius = min(sourceRadius, targetRadius);
        return FORCE_DYNAMICS_PI * minRadius * minRadius;
    }}
    if (centerDistance >= sourceRadius + targetRadius) {{ return 0.0; }}
    if (centerDistance <= abs(sourceRadius - targetRadius)) {{
        float minRadius = min(sourceRadius, targetRadius);
        return FORCE_DYNAMICS_PI * minRadius * minRadius;
    }}

    float sourceTerm = (
        centerDistance * centerDistance + sourceRadius * sourceRadius
        - targetRadius * targetRadius) / (2.0 * centerDistance * sourceRadius);
    float targetTerm = (
        centerDistance * centerDistance + targetRadius * targetRadius
        - sourceRadius * sourceRadius) / (2.0 * centerDistance * targetRadius);
    sourceTerm = clamp(sourceTerm, -1.0, 1.0);
    targetTerm = clamp(targetTerm, -1.0, 1.0);
    float sourceArea = sourceRadius * sourceRadius * acos(sourceTerm);
    float targetArea = targetRadius * targetRadius * acos(targetTerm);
    float triangleArea = 0.5 * sqrt(max(
        0.0,
        (-centerDistance + sourceRadius + targetRadius)
        * (centerDistance + sourceRadius - targetRadius)
        * (centerDistance - sourceRadius + targetRadius)
        * (centerDistance + sourceRadius + targetRadius)));
    return sourceArea + targetArea - triangleArea;
}}

// Python source: ForceDynamics.py:{line("ParticlePenetrationDepth")}
float ParticlePenetrationDepth(float sourceRadius, float targetRadius, float centerDistance)
{{
    return sourceRadius + targetRadius - centerDistance;
}}

bool IsNullParticle(uint ParticleID)
{{
    return ParticleID == 0u && P[ParticleID].ptype < -0.5;
}}

bool IsBoundaryParticle(uint ParticleID)
{{
    return P[ParticleID].ptype > 0.5;
}}

bool IsParticleDead(uint ParticleID)
{{
    return P[ParticleID].Data.w < 0.0;
}}

bool IsParticlePendingBirth(uint ParticleID)
{{
    float stateFlag = P[ParticleID].Data.w;
    if (stateFlag <= 0.0)
    {{
        return false;
    }}
    return float(ShaderFlags.frameNum) < stateFlag;
}}

bool IsParticleBorn(uint ParticleID)
{{
    return !IsParticleDead(ParticleID)
        && !IsParticlePendingBirth(ParticleID);
}}

bool IsParticleActiveForLifecycle(uint ParticleID)
{{
    return !IsNullParticle(ParticleID)
        && IsParticleBorn(ParticleID);
}}

bool IsMobileParticleActiveForDynamics(uint ParticleID)
{{
    return IsParticleActiveForLifecycle(ParticleID)
        && !IsBoundaryParticle(ParticleID);
}}

vec4 GetParticlePosition(uint ParticleID)
{{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[ParticleID].PosLocA
        : P[ParticleID].PosLocB;
}}

vec4 GetNextParticlePosition(uint ParticleID)
{{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[ParticleID].PosLocB
        : P[ParticleID].PosLocA;
}}

void SetNextParticlePosition(uint ParticleID, vec3 position)
{{
    if (uint(ShaderFlags.positionBuffer) == 0u) {{
        P[ParticleID].PosLocB = vec4(position, 0.0);
        P[ParticleID].PosLocA.w = 1.0;
    }} else {{
        P[ParticleID].PosLocA = vec4(position, 0.0);
        P[ParticleID].PosLocB.w = 1.0;
    }}
}}

vec4 GetParticleVelocity(uint ParticleID)
{{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[ParticleID].VelRadA
        : P[ParticleID].VelRadB;
}}

vec4 GetStartFrameVelocity(uint ParticleID)
{{
    return GetParticleVelocity(ParticleID);
}}

vec4 GetNextParticleVelocity(uint ParticleID)
{{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[ParticleID].VelRadB
        : P[ParticleID].VelRadA;
}}

void SetNextParticleVelocity(uint ParticleID, vec4 velocity)
{{
    if (uint(ShaderFlags.positionBuffer) == 0u) {{
        P[ParticleID].VelRadB = velocity;
    }} else {{
        P[ParticleID].VelRadA = velocity;
    }}
}}

bool SetError(uint errorCode)
{{
    uint previous = atomicCompSwap(collOut.ErrorNumber, ERROR_NONE, errorCode);
    if (previous == ERROR_NONE) {{
        collOut.FrameNumber = uint(ShaderFlags.frameNum);
        collOut.ParticleNumber = 0u;
        collOut.holdPidx = 0u;
    }}
    return false;
}}

bool SetError(uint errorCode, uint SourceID)
{{
    uint previous = atomicCompSwap(collOut.ErrorNumber, ERROR_NONE, errorCode);
    if (previous == ERROR_NONE) {{
        collOut.FrameNumber = uint(ShaderFlags.frameNum);
        collOut.ParticleNumber = SourceID;
        collOut.holdPidx = 0u;
    }}
    return false;
}}

bool SetErrorDetail(uint errorCode, uint SourceID, uint detail)
{{
    uint previous = atomicCompSwap(collOut.ErrorNumber, ERROR_NONE, errorCode);
    if (previous == ERROR_NONE) {{
        collOut.FrameNumber = uint(ShaderFlags.frameNum);
        collOut.ParticleNumber = SourceID;
        collOut.holdPidx = detail;
    }}
    return false;
}}

float GetParticleMass(uint ParticleID)
{{
    return max(P[ParticleID].parms.x, EPSILON);
}}

float GetContactTargetDepth(float sourceRadius);
float GetContactHardDepth(float sourceRadius);
float GetContactRemainingDepth(float sourceRadius, float penetrationDepth);

float GetPairStiffness(uint SourceID, uint TargetID)
{{
    return max(0.0, 0.5 * (P[SourceID].Data.y + P[TargetID].Data.y));
}}

float GetContactStiffness(uint SourceID, uint TargetID, uint contactType)
{{
    if (contactType == CONTACT_WALL) {{
        return max(0.0, P[SourceID].Data.y);
    }}
    return GetPairStiffness(SourceID, TargetID);
}}

float GetCompressionStiffnessGain()
{{
    return max(0.0, FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_GAIN);
}}

float GetCompressionStiffnessPower()
{{
    return max(0.0, FORCE_DYNAMICS_SIMPLE_COMPRESSION_STIFFNESS_POWER);
}}

float GetEffectiveContactStiffness(
    float baseStiffness, float penetrationDepth, float sourceRadius)
{{
    float stiffness = max(0.0, baseStiffness);
    float gain = GetCompressionStiffnessGain();
    if (stiffness <= 0.0 || gain <= 0.0) {{
        return stiffness;
    }}

    float hardDepth = GetContactHardDepth(sourceRadius);
    if (hardDepth <= EPSILON) {{
        return stiffness;
    }}

    float compressionFraction = clamp(
        penetrationDepth / hardDepth, 0.0, 1.0);
    return stiffness * (
        1.0 + gain * pow(compressionFraction, GetCompressionStiffnessPower()));
}}

float WallContactOffsetDistance(float radius)
{{
    return min(radius, radius * wall_contact_offset);
}}

ParticleGeometry GetParticleGeometry(uint SourceID, uint TargetID)
{{
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    vec3 targetPosition = GetParticlePosition(TargetID).xyz;
    vec3 delta = targetPosition - sourcePosition;
    float centerDistance = length(delta);
    float sourceRadius = P[SourceID].Data.x;
    float targetRadius = P[TargetID].Data.x;
    if (centerDistance >= sourceRadius + targetRadius) {{
        return ParticleGeometry(vec3(0.0), 0.0, centerDistance,
            sourceRadius, targetRadius, false);
    }}

    vec3 normal = (centerDistance <= EPSILON)
        ? vec3(1.0, 0.0, 0.0)
        : delta / centerDistance;
    float overlapArea = particle_overlap_area(
        sourceRadius, targetRadius, centerDistance);
    return ParticleGeometry(normal, overlapArea, centerDistance,
        sourceRadius, targetRadius, true);
}}

bool CheckPenetrationStepResolution(
    uint SourceID, vec3 normal, float sourceRadius, vec3 targetVelocity)
{{
    vec3 sourceVelocity = GetStartFrameVelocity(SourceID).xyz;
    float relativeNormalVelocity = dot(targetVelocity - sourceVelocity, normal);
    float inwardDisplacement = max(
        0.0, -relativeNormalVelocity * ShaderFlags.dt);
    float penetrationReserve = GetContactHardDepth(sourceRadius);
    if (inwardDisplacement > penetrationReserve + EPSILON) {{
        return SetErrorDetail(ERROR_PENETRATION_STEP_TOO_LARGE, SourceID, 1001u);
    }}
    return true;
}}

float GetContactTargetDepth(float sourceRadius)
{{
    return TARGET_PENETRATION_FRACTION * sourceRadius;
}}

float GetContactHardDepth(float sourceRadius)
{{
    return HARD_PENETRATION_FRACTION * sourceRadius;
}}

float GetContactRemainingDepth(float sourceRadius, float penetrationDepth)
{{
    return GetContactHardDepth(sourceRadius) - penetrationDepth;
}}

float GetContactInwardDisplacement(
    uint SourceID, vec3 normal, vec3 targetVelocity, vec3 sourceVelocity)
{{
    float relativeNormalVelocity = dot(targetVelocity - sourceVelocity, normal);
    return max(0.0, -relativeNormalVelocity * ShaderFlags.dt);
}}

bool CheckResolvedContactStep(
    uint SourceID,
    vec3 normal,
    float penetrationDepth,
    float sourceRadius,
    vec3 targetVelocity)
{{
    float remainingDepth = GetContactRemainingDepth(sourceRadius, penetrationDepth);
    if (penetrationDepth > GetContactHardDepth(sourceRadius) + EPSILON) {{
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9001u);
    }}

    vec3 resolvedVelocity = GetNextParticleVelocity(SourceID).xyz;
    float inwardDisplacement = GetContactInwardDisplacement(
        SourceID,
        normal,
        targetVelocity,
        resolvedVelocity);
    if (inwardDisplacement > remainingDepth + EPSILON) {{
        return SetErrorDetail(ERROR_PENETRATION_STEP_TOO_LARGE, SourceID, 1002u);
    }}
    return true;
}}

bool CheckResolvedParticleContactStep(
    uint SourceID,
    uint TargetID,
    ParticleGeometry geometry)
{{
    if (!geometry.valid) {{ return true; }}
    float penetrationDepth = ParticlePenetrationDepth(
        geometry.sourceRadius,
        geometry.targetRadius,
        geometry.centerDistance);
    return CheckResolvedContactStep(
        SourceID,
        geometry.normal,
        penetrationDepth,
        geometry.sourceRadius,
        GetStartFrameVelocity(TargetID).xyz);
}}

bool CheckResolvedFunctionWallContactStep(
    uint SourceID,
    BoundaryWallSegment segment)
{{
    if (!segment.valid) {{ return true; }}
    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius,
        sourceRadius,
        segment.centerDistance);
    return CheckResolvedContactStep(
        SourceID,
        segment.normal,
        penetrationDepth,
        sourceRadius,
        vec3(0.0));
}}

ParticleGeometry GetPhysicalParticleContact(uint SourceID, uint TargetID)
{{
    ParticleGeometry geometry = GetParticleGeometry(SourceID, TargetID);
    if (!geometry.valid) {{ return geometry; }}

    float physicalProximity =
        geometry.centerDistance - geometry.targetRadius;
    if (physicalProximity < -EPSILON) {{
        SetError(ERROR_PARTICLE_TUNNELING, SourceID);
        return ParticleGeometry(vec3(0.0), 0.0, geometry.centerDistance,
            geometry.sourceRadius, geometry.targetRadius, false);
    }}
    if (!CheckPenetrationStepResolution(
            SourceID,
            geometry.normal,
            geometry.sourceRadius,
            GetStartFrameVelocity(TargetID).xyz)) {{
        return ParticleGeometry(vec3(0.0), 0.0, geometry.centerDistance,
            geometry.sourceRadius, geometry.targetRadius, false);
    }}
    return geometry;
}}

bool RegisterMaximumDepthConstraint(
    uint SourceID,
    vec3 normal,
    float penetrationDepth,
    float sourceRadius,
    vec3 targetVelocity)
{{
    if (maximumDepthConstraintOwner != SourceID) {{
        maximumDepthConstraintOwner = SourceID;
        maximumDepthConstraintCount = 0u;
    }}

    float targetDepth = GetContactTargetDepth(sourceRadius);
    if (penetrationDepth < targetDepth - EPSILON) {{
        return true;
    }}

    float normalLength = length(normal);
    if (normalLength <= MAXIMUM_DEPTH_SOLVER_EPSILON
            || isnan(normalLength) || isinf(normalLength)
            || any(isnan(targetVelocity)) || any(isinf(targetVelocity))) {{
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9002u);
    }}
    vec3 unitNormal = normal / normalLength;
    float limit = dot(targetVelocity, unitNormal);
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {{
        float alignment = dot(
            maximumDepthConstraintNormals[index], unitNormal);
        if (alignment >= 1.0 - MAXIMUM_DEPTH_SOLVER_EPSILON) {{
            maximumDepthConstraintLimits[index] = min(
                maximumDepthConstraintLimits[index], limit);
            return true;
        }}
    }}

    if (maximumDepthConstraintCount >= MAX_SOURCE_DEPTH_CONSTRAINTS) {{
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9003u);
    }}
    maximumDepthConstraintNormals[maximumDepthConstraintCount] = unitNormal;
    maximumDepthConstraintLimits[maximumDepthConstraintCount] = limit;
    maximumDepthConstraintCount += 1u;
    return true;
}}

bool RegisterContactStepConstraint(
    uint SourceID,
    vec3 normal,
    float penetrationDepth,
    float sourceRadius,
    vec3 targetVelocity)
{{
    if (maximumDepthConstraintOwner != SourceID) {{
        maximumDepthConstraintOwner = SourceID;
        maximumDepthConstraintCount = 0u;
    }}

    float hardDepth = GetContactHardDepth(sourceRadius);
    if (penetrationDepth > hardDepth + EPSILON) {{
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9001u);
    }}

    float dt = ShaderFlags.dt;
    if (dt <= 0.0) {{ return SetError(ERROR_INVALID_DT, SourceID); }}

    float normalLength = length(normal);
    if (normalLength <= MAXIMUM_DEPTH_SOLVER_EPSILON
            || isnan(normalLength) || isinf(normalLength)
            || any(isnan(targetVelocity)) || any(isinf(targetVelocity))) {{
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9002u);
    }}

    vec3 unitNormal = normal / normalLength;
    float remainingDepth = max(0.0, hardDepth - penetrationDepth);
    float limit = dot(targetVelocity, unitNormal) + remainingDepth / dt;
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {{
        float alignment = dot(
            maximumDepthConstraintNormals[index], unitNormal);
        if (alignment >= 1.0 - MAXIMUM_DEPTH_SOLVER_EPSILON) {{
            maximumDepthConstraintLimits[index] = min(
                maximumDepthConstraintLimits[index], limit);
            return true;
        }}
    }}

    if (maximumDepthConstraintCount >= MAX_SOURCE_DEPTH_CONSTRAINTS) {{
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, 9003u);
    }}
    maximumDepthConstraintNormals[maximumDepthConstraintCount] = unitNormal;
    maximumDepthConstraintLimits[maximumDepthConstraintCount] = limit;
    maximumDepthConstraintCount += 1u;
    return true;
}}

bool SolveMaximumDepthSystem(
    mat3 matrix,
    vec3 values,
    uint size,
    out vec3 solution)
{{
    solution = vec3(0.0);
    if (size == 1u) {{
        if (abs(matrix[0][0]) <= MAXIMUM_DEPTH_SOLVER_EPSILON) {{
            return false;
        }}
        solution.x = values.x / matrix[0][0];
        return !any(isnan(solution)) && !any(isinf(solution));
    }}
    if (size == 2u) {{
        float det = matrix[0][0] * matrix[1][1]
            - matrix[1][0] * matrix[0][1];
        if (abs(det) <= MAXIMUM_DEPTH_SOLVER_EPSILON) {{
            return false;
        }}
        solution.x = (values.x * matrix[1][1]
            - matrix[1][0] * values.y) / det;
        solution.y = (matrix[0][0] * values.y
            - values.x * matrix[0][1]) / det;
        return !any(isnan(solution)) && !any(isinf(solution));
    }}
    return false;
}}

bool AccumulateContactForce(
    uint SourceID, ContactForceInput contact, inout vec3 totalForce)
{{
    if (!contact.valid) {{ return true; }}
    float baseStiffness = GetContactStiffness(
        SourceID, contact.targetID, contact.contactType);
    float stiffness = GetEffectiveContactStiffness(
        baseStiffness,
        max(0.0, contact.penetrationDepth),
        P[SourceID].Data.x);
    float forceMagnitude = stiffness * max(0.0, contact.penetrationDepth);
    totalForce -= forceMagnitude * contact.normal;
    P[SourceID].colFlg = 1u;
    return true;
}}

bool ProcessParticleCollision(
    uint TargetID,
    uint SourceID,
    inout vec3 totalForce,
    ParticleGeometry geometry)
{{
    if (!geometry.valid) {{ return true; }}
    float penetrationDepth = ParticlePenetrationDepth(
        geometry.sourceRadius,
        geometry.targetRadius,
        geometry.centerDistance);
    if (!RegisterMaximumDepthConstraint(
            SourceID,
            geometry.normal,
            penetrationDepth,
            geometry.sourceRadius,
            GetStartFrameVelocity(TargetID).xyz)) {{
        return false;
    }}
    P[SourceID].contactCount += 1u;
    ContactForceInput contact = ContactForceInput(
        TargetID,
        CONTACT_PARTICLE,
        geometry.normal,
        geometry.overlapArea,
        penetrationDepth,
        GetStartFrameVelocity(TargetID).xyz,
        true);
    return AccumulateContactForce(SourceID, contact, totalForce);
}}

bool ProcessFunctionWallCollision(
    uint SourceID, BoundaryWallSegment segment, inout vec3 totalForce)
{{
    if (!segment.valid) {{ return true; }}
    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius, sourceRadius, segment.centerDistance);
    float maximumDepthDistance =
        sourceRadius - WallContactOffsetDistance(sourceRadius);
    if (segment.centerDistance - maximumDepthDistance < -EPSILON) {{
        return SetError(ERROR_WALL_TUNNELING, SourceID);
    }}
    if (!CheckPenetrationStepResolution(
            SourceID, segment.normal, sourceRadius, vec3(0.0))) {{
        return false;
    }}
    if (!RegisterMaximumDepthConstraint(
            SourceID,
            segment.normal,
            penetrationDepth,
            sourceRadius,
            vec3(0.0))) {{
        return false;
    }}
    P[SourceID].contactCount += 1u;
    ContactForceInput contact = ContactForceInput(
        segment.wallFlag,
        CONTACT_WALL,
        segment.normal,
        segment.overlapArea,
        penetrationDepth,
        vec3(0.0),
        true);
    return AccumulateContactForce(SourceID, contact, totalForce);
}}

bool RegisterResolvedParticleContactStep(
    uint SourceID,
    uint TargetID,
    ParticleGeometry geometry)
{{
    if (!geometry.valid) {{ return true; }}
    float penetrationDepth = ParticlePenetrationDepth(
        geometry.sourceRadius,
        geometry.targetRadius,
        geometry.centerDistance);
    return RegisterContactStepConstraint(
        SourceID,
        geometry.normal,
        penetrationDepth,
        geometry.sourceRadius,
        GetStartFrameVelocity(TargetID).xyz);
}}

bool RegisterResolvedFunctionWallContactStep(
    uint SourceID,
    BoundaryWallSegment segment)
{{
    if (!segment.valid) {{ return true; }}
    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius,
        sourceRadius,
        segment.centerDistance);
    return RegisterContactStepConstraint(
        SourceID,
        segment.normal,
        penetrationDepth,
        sourceRadius,
        vec3(0.0));
}}

bool ProjectSourceVelocityToContactSet(
    vec3 candidateVelocity, out vec3 containedVelocity)
{{
    containedVelocity = candidateVelocity;
    if (any(isnan(candidateVelocity)) || any(isinf(candidateVelocity))) {{
        return false;
    }}

    bool candidateValid = true;
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {{
        if (dot(maximumDepthConstraintNormals[index], candidateVelocity)
                > maximumDepthConstraintLimits[index]
                    + MAXIMUM_DEPTH_SOLVER_EPSILON) {{
            candidateValid = false;
        }}
    }}
    if (candidateValid) {{
        return true;
    }}

    bool found = false;
    float bestDistanceSq = 0.0;
    for (uint i = 0u; i < maximumDepthConstraintCount; ++i) {{
        for (uint jCode = 0u; jCode <= maximumDepthConstraintCount; ++jCode) {{
            uint activeCount = 1u;
            uint j = 0u;
            if (jCode > 0u) {{
                j = jCode - 1u;
                if (j <= i) {{ continue; }}
                activeCount = 2u;
            }}

            vec3 n0 = maximumDepthConstraintNormals[i];
            vec3 n1 = activeCount == 2u
                ? maximumDepthConstraintNormals[j] : vec3(0.0);
            vec3 limits = vec3(
                maximumDepthConstraintLimits[i],
                activeCount == 2u ? maximumDepthConstraintLimits[j] : 0.0,
                0.0);
            mat3 gram = mat3(0.0);
            gram[0][0] = dot(n0, n0);
            if (activeCount == 2u) {{
                gram[0][1] = dot(n0, n1);
                gram[1][0] = gram[0][1];
                gram[1][1] = dot(n1, n1);
            }}
            vec3 residual = vec3(
                dot(n0, candidateVelocity),
                activeCount == 2u ? dot(n1, candidateVelocity) : 0.0,
                0.0) - limits;
            vec3 multipliers;
            if (!SolveMaximumDepthSystem(
                    gram, residual, activeCount, multipliers)) {{
                continue;
            }}
            if (multipliers.x < -MAXIMUM_DEPTH_SOLVER_EPSILON
                    || (activeCount == 2u
                        && multipliers.y < -MAXIMUM_DEPTH_SOLVER_EPSILON)) {{
                continue;
            }}
            vec3 velocity = candidateVelocity - multipliers.x * n0;
            if (activeCount == 2u) {{ velocity -= multipliers.y * n1; }}
            if (any(isnan(velocity)) || any(isinf(velocity))) {{ continue; }}
            bool satisfiesAll = true;
            for (uint constraint = 0u;
                    constraint < maximumDepthConstraintCount;
                    ++constraint) {{
                if (dot(maximumDepthConstraintNormals[constraint], velocity)
                        > maximumDepthConstraintLimits[constraint]
                            + MAXIMUM_DEPTH_SOLVER_EPSILON) {{
                    satisfiesAll = false;
                }}
            }}
            if (!satisfiesAll) {{ continue; }}
            float distanceSq = dot(
                candidateVelocity - velocity,
                candidateVelocity - velocity);
            if (isnan(distanceSq) || isinf(distanceSq)) {{ continue; }}
            if (!found || distanceSq < bestDistanceSq) {{
                found = true;
                bestDistanceSq = distanceSq;
                containedVelocity = velocity;
            }}
        }}
    }}
    return found;
}}

bool ApplySourceMaximumDepth(uint SourceID, uint failureDetail)
{{
    if (maximumDepthConstraintOwner != SourceID
            || maximumDepthConstraintCount == 0u) {{
        return true;
    }}

    vec4 candidate = GetNextParticleVelocity(SourceID);
    vec3 containedVelocity = vec3(0.0);
    if (!ProjectSourceVelocityToContactSet(
            candidate.xyz, containedVelocity)) {{
        return SetErrorDetail(ERROR_MAX_DEPTH_CONSTRAINT, SourceID, failureDetail);
    }}
    candidate.xyz = containedVelocity;
    candidate.w = VelocityAngle(candidate.x, candidate.y);
    SetNextParticleVelocity(SourceID, candidate);
    return true;
}}

bool CalcVelocity(uint SourceID, vec3 totalForce)
{{
    float dt = ShaderFlags.dt;
    if (dt <= 0.0) {{ return SetError(ERROR_INVALID_DT, SourceID); }}
    float mass = GetParticleMass(SourceID);
    vec4 startVelocity = GetStartFrameVelocity(SourceID);
    vec4 nextVelocity = startVelocity;
    nextVelocity.xyz = startVelocity.xyz + totalForce * dt / mass;
    nextVelocity.w = VelocityAngle(nextVelocity.x, nextVelocity.y);
    SetNextParticleVelocity(SourceID, nextVelocity);
    return true;
}}

bool CalcPosition(uint SourceID)
{{
    float dt = ShaderFlags.dt;
    if (dt <= 0.0) {{ return SetError(ERROR_INVALID_DT, SourceID); }}

    vec4 position = GetParticlePosition(SourceID);
    vec4 velocity = GetNextParticleVelocity(SourceID);
    vec3 nextPosition = position.xyz + velocity.xyz * dt;

    if (nextPosition.x < 0.0 || nextPosition.x >= float(WIDTH)
            || nextPosition.y < 0.0 || nextPosition.y >= float(HEIGHT)
            || nextPosition.z < 0.0 || nextPosition.z >= float(DEPTH)) {{
        return SetError(ERROR_PARTICLE_OUT_OF_BOUNDS, SourceID);
    }}

    if (uint(ShaderFlags.positionBuffer) == 0u) {{
        P[SourceID].PosLocB = vec4(nextPosition, 0.0);
        P[SourceID].PosLocA.w = 1.0;
    }} else {{
        P[SourceID].PosLocA = vec4(nextPosition, 0.0);
        P[SourceID].PosLocB.w = 1.0;
    }}

    if (nextPosition.x < death_x_min || nextPosition.x > death_x_max
            || nextPosition.y < death_y_min || nextPosition.y > death_y_max
            || nextPosition.z < death_z_min || nextPosition.z > death_z_max) {{
        P[SourceID].Data.w = -1.0;
    }}
    return true;
}}

#endif
"""


def render_boundary(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    line = lambda name: method_line(visitor, name)
    return f"""#ifndef FORCE_DYNAMICS_SIMPLE_BOUNDARY_PARTICLE_GLSL
#define FORCE_DYNAMICS_SIMPLE_BOUNDARY_PARTICLE_GLSL

// Generated from {source_path.as_posix()} by tools/ExportForceDynamicsSimpleGLSL.py.
// Boundary-particle locality helpers for the simple generic model.
// Do not hand edit generated dynamics content.

// Python source: ForceDynamics.py:{line("BoundaryMarkerApplies")}
bool BoundaryMarkerApplies(uint SourceID, uint BoundaryID)
{{
    if (!IsBoundaryParticle(BoundaryID)) {{ return false; }}
    vec4 sourcePosition = GetParticlePosition(SourceID);
    vec4 boundaryPosition = GetParticlePosition(BoundaryID);
    return abs(sourcePosition.x - boundaryPosition.x) <= 1.0
        && abs(sourcePosition.y - boundaryPosition.y) <= 1.0
        && abs(sourcePosition.z - boundaryPosition.z) <= 1.0;
}}

bool ProcessFunctionWallCollision(
    uint SourceID, BoundaryWallSegment segment, inout vec3 totalForce);

#endif
"""


def render_function_wall(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    line = lambda name: method_line(visitor, name)
    return f"""#ifndef FORCE_DYNAMICS_SIMPLE_FUNCTION_WALL_GLSL
#define FORCE_DYNAMICS_SIMPLE_FUNCTION_WALL_GLSL

// Generated from {source_path.as_posix()} by tools/ExportForceDynamicsSimpleGLSL.py.
// Function-wall evaluator for the simple generic model.
// Do not hand edit generated dynamics content.

vec2 FunctionWallValueSlope(FunctionWallSegment segment, float u)
{{
    float du = u - segment.uStart;
    float du2 = du * du;
    float value = segment.fStart
        + segment.a1 * du
        + segment.a2 * du2
        + segment.a3 * du2 * du;
    float slope = segment.a1
        + 2.0 * segment.a2 * du
        + 3.0 * segment.a3 * du2;
    return vec2(value, slope);
}}

bool FunctionWallEvaluateAtPoint(
    FunctionWallSegment segment,
    vec2 point,
    out vec2 wallPoint,
    out vec2 normal)
{{
    float u = point.x;
    if (segment.independentAxis == 1u) {{
        u = point.y;
    }}

    float lower = min(segment.uStart, segment.uEnd);
    float upper = max(segment.uStart, segment.uEnd);
    if (u < lower - EPSILON || u > upper + EPSILON) {{
        return false;
    }}

    vec2 valueSlope = FunctionWallValueSlope(segment, u);
    if (segment.independentAxis == 0u) {{
        wallPoint = vec2(u, valueSlope.x);
        if (segment.normalSign >= 0.0) {{
            normal = normalize(vec2(-valueSlope.y, 1.0));
        }} else {{
            normal = normalize(vec2(valueSlope.y, -1.0));
        }}
    }} else {{
        wallPoint = vec2(valueSlope.x, u);
        if (segment.normalSign >= 0.0) {{
            normal = normalize(vec2(1.0, -valueSlope.y));
        }} else {{
            normal = normalize(vec2(-1.0, valueSlope.y));
        }}
    }}
    return !(any(isnan(wallPoint))
        || any(isinf(wallPoint))
        || any(isnan(normal))
        || any(isinf(normal)));
}}

float FunctionWallPhysicalPenetration(
    FunctionWallSegment segment,
    vec2 point,
    float radius)
{{
    vec2 wallPoint;
    vec2 normal;
    if (!FunctionWallEvaluateAtPoint(segment, point, wallPoint, normal)) {{
        return -1.0;
    }}
    float signedOutwardDistance = dot(point - wallPoint, normal);
    return radius + signedOutwardDistance;
}}

FunctionWallSegment SelectFunctionWallSegment(uint SourceID, uint BoundaryID)
{{
    vec2 marker = GetParticlePosition(BoundaryID).xy;
    FunctionWallSegment selected = CURVE_WALL_SEGMENTS[0];
    float bestDistanceSq = 3.402823466e+38;
    for (uint index = 0u; index < CURVE_WALL_SEGMENT_COUNT; ++index) {{
        FunctionWallSegment candidate = CURVE_WALL_SEGMENTS[index];
        vec2 wallPoint;
        vec2 normal;
        if (!FunctionWallEvaluateAtPoint(candidate, marker, wallPoint, normal)) {{
            continue;
        }}
        float distanceSq = dot(wallPoint - marker, wallPoint - marker);
        if (distanceSq < bestDistanceSq) {{
            bestDistanceSq = distanceSq;
            selected = candidate;
        }}
    }}
    return selected;
}}

// Python source: ForceDynamics.py:{line("EvaluateFunctionWallSegment")}
BoundaryWallSegment EvaluateFunctionWallSegment(uint SourceID, uint BoundaryID)
{{
    FunctionWallSegment selected = SelectFunctionWallSegment(SourceID, BoundaryID);
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    vec2 wallPoint;
    vec2 normal2d;
    if (!FunctionWallEvaluateAtPoint(selected, sourcePosition.xy, wallPoint, normal2d)) {{
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, selected.wallFlag, false);
    }}

    float radius = P[SourceID].Data.x;
    float penetrationDepth = FunctionWallPhysicalPenetration(
        selected,
        sourcePosition.xy,
        radius);
    if (penetrationDepth <= EPSILON) {{
        float centerDistance = max(0.0, 2.0 * radius - penetrationDepth);
        return BoundaryWallSegment(
            vec3(normal2d, 0.0),
            0.0,
            centerDistance,
            selected.wallFlag,
            false);
    }}

    float centerDistance = max(0.0, 2.0 * radius - penetrationDepth);
    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(
        vec3(normal2d, 0.0),
        overlapArea,
        centerDistance,
        selected.wallFlag,
        true);
}}

#endif
"""


def render_rectangle_wall(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    line = lambda name: method_line(visitor, name)
    return f"""#ifndef FORCE_DYNAMICS_SIMPLE_RECTANGLE_WALL_GLSL
#define FORCE_DYNAMICS_SIMPLE_RECTANGLE_WALL_GLSL

// Generated from {source_path.as_posix()} by tools/ExportForceDynamicsSimpleGLSL.py.
// Rectangle-wall evaluator for the simple generic 3D model.
// Do not hand edit generated dynamics content.

bool RectangleWallProjectPoint(
    RectangleWallSegment segment,
    vec3 point,
    out float uCoord,
    out float vCoord,
    out float signedInwardDistance)
{{
    vec3 inwardNormal = normalize(segment.inwardNormal);
    if (any(isnan(inwardNormal)) || any(isinf(inwardNormal))) {{
        return false;
    }}

    vec3 rel = point - segment.origin;
    uCoord = dot(rel, segment.uAxis);
    vCoord = dot(rel, segment.vAxis);
    if (uCoord < -EPSILON || uCoord > segment.uLength + EPSILON) {{
        return false;
    }}
    if (vCoord < -EPSILON || vCoord > segment.vLength + EPSILON) {{
        return false;
    }}

    signedInwardDistance = dot(rel, inwardNormal);
    return true;
}}

float RectangleWallPhysicalPenetration(
    RectangleWallSegment segment,
    vec3 point,
    float radius)
{{
    float uCoord = 0.0;
    float vCoord = 0.0;
    float signedInwardDistance = 0.0;
    if (!RectangleWallProjectPoint(
            segment,
            point,
            uCoord,
            vCoord,
            signedInwardDistance)) {{
        return -1.0;
    }}
    return radius - signedInwardDistance;
}}

RectangleWallSegment SelectRectangleWallSegment(uint SourceID, uint BoundaryID)
{{
    vec3 marker = GetParticlePosition(BoundaryID).xyz;
    RectangleWallSegment selected = RECTANGLE_WALL_SEGMENTS[0];
    float bestDistance = 3.402823466e+38;
    for (uint index = 0u; index < RECTANGLE_WALL_SEGMENT_COUNT; ++index) {{
        RectangleWallSegment candidate = RECTANGLE_WALL_SEGMENTS[index];
        float uCoord = 0.0;
        float vCoord = 0.0;
        float signedInwardDistance = 0.0;
        if (!RectangleWallProjectPoint(
                candidate,
                marker,
                uCoord,
                vCoord,
                signedInwardDistance)) {{
            continue;
        }}

        float distance = abs(signedInwardDistance);
        if (distance < bestDistance) {{
            bestDistance = distance;
            selected = candidate;
        }}
    }}
    return selected;
}}

// Python source: ForceDynamics.py:{line("EvaluateRectangleWallSegment")}
BoundaryWallSegment EvaluateRectangleWallSegment(uint SourceID, uint BoundaryID)
{{
    RectangleWallSegment selected = SelectRectangleWallSegment(SourceID, BoundaryID);
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    float radius = P[SourceID].Data.x;
    float penetrationDepth = RectangleWallPhysicalPenetration(
        selected,
        sourcePosition,
        radius);

    vec3 inwardNormal = normalize(selected.inwardNormal);
    vec3 forcePathNormal = -inwardNormal;
    if (penetrationDepth <= EPSILON
        || any(isnan(forcePathNormal))
        || any(isinf(forcePathNormal))) {{
        float centerDistance = max(0.0, 2.0 * radius - penetrationDepth);
        return BoundaryWallSegment(
            forcePathNormal,
            0.0,
            centerDistance,
            selected.wallFlag,
            false);
    }}

    float centerDistance = max(0.0, 2.0 * radius - penetrationDepth);
    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(
        forcePathNormal,
        overlapArea,
        centerDistance,
        selected.wallFlag,
        true);
}}

#endif
"""


def render_lighting_ball(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    line = lambda name: method_line(visitor, name)
    return f"""#ifndef FORCE_DYNAMICS_SIMPLE_LIGHTING_BALL_GLSL
#define FORCE_DYNAMICS_SIMPLE_LIGHTING_BALL_GLSL

// Generated from {source_path.as_posix()} by tools/ExportForceDynamicsSimpleGLSL.py.
// Analytic lighting-ball sphere evaluator for the simple generic 3D model.
// Do not hand edit generated dynamics content.

struct LightingBallCollisionResult
{{
    bool handled;
    bool ok;
    BoundaryWallSegment segment;
}};

bool IsLightingBallMarker(uint BoundaryID)
{{
    if (LIGHTING_BALL_ENABLED == 0u || !IsBoundaryParticle(BoundaryID)) {{
        return false;
    }}
    uint materialID = uint(round(P[BoundaryID].material_id));
    return materialID == LIGHTING_BALL_MATERIAL_ID;
}}

LightingBallCollisionResult NoLightingBallCollision()
{{
    return LightingBallCollisionResult(
        false,
        true,
        BoundaryWallSegment(vec3(0.0), 0.0, 0.0, LIGHTING_BALL_WALL_FLAG, false));
}}

// Python source: ForceDynamics.py:{line("EvaluateLightingBallContact")}
BoundaryWallSegment EvaluateLightingBallContact(uint SourceID)
{{
    if (LIGHTING_BALL_ENABLED == 0u || LIGHTING_BALL_RADIUS <= 0.0) {{
        return BoundaryWallSegment(
            vec3(0.0),
            0.0,
            0.0,
            LIGHTING_BALL_WALL_FLAG,
            false);
    }}

    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    vec3 delta = sourcePosition - LIGHTING_BALL_CENTER;
    float centerDistance = length(delta);
    if (centerDistance <= EPSILON
            || isnan(centerDistance)
            || isinf(centerDistance)) {{
        return BoundaryWallSegment(
            vec3(0.0),
            0.0,
            0.0,
            LIGHTING_BALL_WALL_FLAG,
            false);
    }}

    float sourceRadius = P[SourceID].Data.x;
    float signedSurfaceDistance = centerDistance - LIGHTING_BALL_RADIUS;
    float penetrationDepth = sourceRadius - signedSurfaceDistance;
    if (penetrationDepth <= EPSILON) {{
        float contactCenterDistance =
            max(0.0, 2.0 * sourceRadius - penetrationDepth);
        return BoundaryWallSegment(
            delta / centerDistance,
            0.0,
            contactCenterDistance,
            LIGHTING_BALL_WALL_FLAG,
            false);
    }}

    vec3 normal = delta / centerDistance;
    float contactCenterDistance =
        max(0.0, 2.0 * sourceRadius - penetrationDepth);
    float overlapArea = particle_overlap_area(
        sourceRadius,
        sourceRadius,
        contactCenterDistance);
    return BoundaryWallSegment(
        normal,
        overlapArea,
        contactCenterDistance,
        LIGHTING_BALL_WALL_FLAG,
        true);
}}

// Python source: ForceDynamics.py:{line("ProcessLightingBallCollision")}
LightingBallCollisionResult ProcessLightingBallCollision(
    uint SourceID,
    inout vec3 totalForce)
{{
    totalForce += vec3(0.0);
    BoundaryWallSegment segment = EvaluateLightingBallContact(SourceID);
    if (!segment.valid) {{
        return NoLightingBallCollision();
    }}

    P[SourceID].colFlg = 1u;
    if (IsPhotonParticle(SourceID)) {{
        P[SourceID].material_id = float(LIGHTING_BALL_MATERIAL_ID);
    }}
    vec3 startVelocity = GetStartFrameVelocity(SourceID).xyz;
    float inwardSpeed = -dot(startVelocity, segment.normal);
    if (inwardSpeed <= EPSILON) {{
        return NoLightingBallCollision();
    }}

    return LightingBallCollisionResult(true, true, segment);
}}

bool RegisterResolvedLightingBallContactStep(uint SourceID)
{{
    return true;
}}

#endif
"""


def render_piston(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    line = lambda name: method_line(visitor, name)
    return f"""#ifndef FORCE_DYNAMICS_SIMPLE_PISTON_GLSL
#define FORCE_DYNAMICS_SIMPLE_PISTON_GLSL

// Generated from {source_path.as_posix()} by tools/ExportForceDynamicsSimpleGLSL.py.
// Optional analytic piston support for packed reservoir tests.
// Do not hand edit generated dynamics content.

#if defined(FORCE_DYNAMICS_SIMPLE_PISTON_AVAILABLE)

// Python source: ForceDynamics.py:{line("PistonEnabled")}
bool PistonEnabled()
{{
    return true;
}}

// Python source: ForceDynamics.py:{line("GetPistonPosition")}
float GetPistonPosition(uint frame)
{{
    uint pistonStartFrame = uint(piston_start_frame);
    if (frame < pistonStartFrame) {{
        return piston_x_start;
    }}

    float elapsedFrames = float(frame - pistonStartFrame);
    vec3 pistonVelocity = vec3(
        piston_velocity_x,
        piston_velocity_y,
        piston_velocity_z);
    float position = piston_x_start
        + elapsedFrames * ShaderFlags.dt * pistonVelocity.x;
    return min(position, piston_x_stop);
}}

// Python source: ForceDynamics.py:{line("GetPistonVelocity")}
vec3 GetPistonVelocity(uint frame)
{{
    uint pistonStartFrame = uint(piston_start_frame);
    if (frame < pistonStartFrame) {{
        return vec3(0.0);
    }}
    if (GetPistonPosition(frame) >= piston_x_stop) {{
        return vec3(0.0);
    }}
    return vec3(
        piston_velocity_x,
        piston_velocity_y,
        piston_velocity_z);
}}

// Python source: ForceDynamics.py:{line("EvaluatePistonWall")}
BoundaryWallSegment EvaluatePistonWall(uint SourceID)
{{
    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    float radius = P[SourceID].Data.x;
    float offset = WallContactOffsetDistance(radius);
    float pistonX = GetPistonPosition(uint(ShaderFlags.frameNum));
    vec3 ghost = vec3(
        pistonX - radius + offset,
        sourcePosition.y,
        sourcePosition.z);
    vec3 normal = vec3(-1.0, 0.0, 0.0);
    float centerDistance = abs(ghost.x - sourcePosition.x);
    if (centerDistance >= 2.0 * radius) {{
        return BoundaryWallSegment(normal, 0.0, centerDistance, 1u, false);
    }}

    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(normal, overlapArea, centerDistance, 1u, true);
}}

// Python source: ForceDynamics.py:{line("ProcessPistonCollision")}
bool ProcessPistonCollision(uint SourceID, inout vec3 totalForce)
{{
    if (!PistonEnabled()) {{ return true; }}

    BoundaryWallSegment segment = EvaluatePistonWall(SourceID);
    if (!segment.valid) {{ return true; }}

    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius, sourceRadius, segment.centerDistance);
    float maximumDepthDistance =
        sourceRadius - WallContactOffsetDistance(sourceRadius);
    if (segment.centerDistance - maximumDepthDistance < -EPSILON) {{
        return SetError(ERROR_WALL_TUNNELING, SourceID);
    }}

    vec3 pistonVelocity = GetPistonVelocity(uint(ShaderFlags.frameNum));
    if (!CheckPenetrationStepResolution(
            SourceID, segment.normal, sourceRadius, pistonVelocity)) {{
        return false;
    }}
    if (!RegisterMaximumDepthConstraint(
            SourceID,
            segment.normal,
            penetrationDepth,
            sourceRadius,
            pistonVelocity)) {{
        return false;
    }}

    P[SourceID].contactCount += 1u;
    ContactForceInput contact = ContactForceInput(
        segment.wallFlag,
        CONTACT_WALL,
        segment.normal,
        segment.overlapArea,
        penetrationDepth,
        pistonVelocity,
        true);
    return AccumulateContactForce(SourceID, contact, totalForce);
}}

bool CheckResolvedPistonContactStep(uint SourceID)
{{
    if (!PistonEnabled()) {{ return true; }}

    BoundaryWallSegment segment = EvaluatePistonWall(SourceID);
    if (!segment.valid) {{ return true; }}

    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius,
        sourceRadius,
        segment.centerDistance);
    return CheckResolvedContactStep(
        SourceID,
        segment.normal,
        penetrationDepth,
        sourceRadius,
        GetPistonVelocity(uint(ShaderFlags.frameNum)));
}}

bool RegisterResolvedPistonContactStep(uint SourceID)
{{
    if (!PistonEnabled()) {{ return true; }}

    BoundaryWallSegment segment = EvaluatePistonWall(SourceID);
    if (!segment.valid) {{ return true; }}

    float sourceRadius = P[SourceID].Data.x;
    float penetrationDepth = ParticlePenetrationDepth(
        sourceRadius,
        sourceRadius,
        segment.centerDistance);
    return RegisterContactStepConstraint(
        SourceID,
        segment.normal,
        penetrationDepth,
        sourceRadius,
        GetPistonVelocity(uint(ShaderFlags.frameNum)));
}}

#endif

#endif
"""


def render_photons() -> str:
    return """#ifndef PHOTONS_GLSL
#define PHOTONS_GLSL

// Generated by tools/ExportForceDynamicsSimpleGLSL.py.
// Optical photon helpers shared by generated simple Vulkan force shaders.

const float PTYPE_PHOTON = -2.0;

uint GetParticleType(uint particleID)
{
    if (int(round(P[particleID].ptype)) == int(PTYPE_PHOTON)) {
        return PARTICLE_TYPE_PHOTON;
    }
    return PARTICLE_TYPE_REGULAR;
}

bool IsPhotonParticle(uint particleID)
{
    return GetParticleType(particleID) == PARTICLE_TYPE_PHOTON;
}

uint PhotonBaseMaterialID()
{
    for (uint ii = 0u; ii < MATERIAL_PROPERTY_COUNT; ++ii) {
        if (MATERIAL_PROPERTIES[ii].particleType == PARTICLE_TYPE_PHOTON) {
            return MATERIAL_PROPERTIES[ii].materialID;
        }
    }
    return 0u;
}

bool ShouldSkipParticlePair(uint sourceID, uint targetID)
{
    bool sourcePhoton = IsPhotonParticle(sourceID);
    bool targetPhoton = IsPhotonParticle(targetID);
    return (sourcePhoton && targetPhoton) || (!sourcePhoton && targetPhoton);
}

vec3 ReflectFixedSpeed(vec3 velocity, vec3 normal)
{
    float speed = length(velocity);
    float normalLength = length(normal);
    if (speed <= 0.0 || normalLength <= 0.0) {
        return velocity;
    }

    vec3 unitNormal = normal / normalLength;
    vec3 reflected = velocity - 2.0 * dot(velocity, unitNormal) * unitNormal;
    float reflectedLength = length(reflected);
    if (reflectedLength <= 0.0) {
        return velocity;
    }
    return speed * reflected / reflectedLength;
}

struct PhotonParticleReflection
{
    bool reflected;
    vec3 velocity;
    vec3 position;
};

vec3 PhotonStartPosition(uint particleID)
{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[particleID].PosLocA.xyz
        : P[particleID].PosLocB.xyz;
}

vec3 PhotonStartVelocity(uint particleID)
{
    return uint(ShaderFlags.positionBuffer) == 0u
        ? P[particleID].VelRadA.xyz
        : P[particleID].VelRadB.xyz;
}

PhotonParticleReflection NoPhotonParticleReflection(uint sourceID)
{
    return PhotonParticleReflection(
        false,
        PhotonStartVelocity(sourceID),
        PhotonStartPosition(sourceID));
}

PhotonParticleReflection RecordPhotonParticleReflection(
    uint sourceID,
    uint targetID,
    vec3 normal,
    float hitT)
{
    float dt = ShaderFlags.dt;
    vec3 targetPosition = PhotonStartPosition(targetID);
    vec3 targetVelocity = PhotonStartVelocity(targetID);
    vec3 sourceVelocity = PhotonStartVelocity(sourceID);
    vec3 reflectedVelocity = ReflectFixedSpeed(sourceVelocity, normal);
    float boundedHitT = clamp(hitT, 0.0, 1.0);
    vec3 targetHitPosition = targetPosition + targetVelocity * dt * boundedHitT;
    float sourceRadius = P[sourceID].Data.x;
    float targetRadius = P[targetID].Data.x;
    float contactRadius = sourceRadius + targetRadius;
    vec3 hitPosition = targetHitPosition - normal * contactRadius;
    float remainingDt = dt * (1.0 - boundedHitT);
    float exitEpsilon = max(1.0e-12, sourceRadius * 0.01);
    vec3 outputPosition =
        hitPosition + reflectedVelocity * remainingDt - normal * exitEpsilon;
    return PhotonParticleReflection(true, reflectedVelocity, outputPosition);
}

bool TryPhotonParticleReflection(
    uint sourceID,
    uint targetID,
    out PhotonParticleReflection reflection)
{
    reflection = NoPhotonParticleReflection(sourceID);
    if (!IsPhotonParticle(sourceID) || IsPhotonParticle(targetID)) {
        return false;
    }

    float dt = ShaderFlags.dt;
    if (dt <= 0.0) {
        return false;
    }

    vec3 sourcePosition = PhotonStartPosition(sourceID);
    vec3 targetPosition = PhotonStartPosition(targetID);
    vec3 sourceVelocity = PhotonStartVelocity(sourceID);
    vec3 targetVelocity = PhotonStartVelocity(targetID);
    vec3 relativeMotion = (sourceVelocity - targetVelocity) * dt;
    float motionLengthSq = dot(relativeMotion, relativeMotion);
    if (motionLengthSq <= 1.0e-12) {
        return false;
    }

    vec3 startDelta = sourcePosition - targetPosition;
    float sourceRadius = P[sourceID].Data.x;
    float targetRadius = P[targetID].Data.x;
    float contactRadius = sourceRadius + targetRadius;
    float contactRadiusSq = contactRadius * contactRadius;
    float startDistanceSq = dot(startDelta, startDelta);
    float hitT = 0.0;
    vec3 normal = vec3(1.0, 0.0, 0.0);

    if (startDistanceSq < contactRadiusSq) {
        float centerDistance = sqrt(max(startDistanceSq, 0.0));
        if (centerDistance > 1.0e-12) {
            normal = -startDelta / centerDistance;
        }
    } else {
        float a = motionLengthSq;
        float b = 2.0 * dot(startDelta, relativeMotion);
        float c = startDistanceSq - contactRadiusSq;
        float discriminant = b * b - 4.0 * a * c;
        if (discriminant < 0.0) {
            return false;
        }
        float sqrtDiscriminant = sqrt(discriminant);
        float firstT = (-b - sqrtDiscriminant) / (2.0 * a);
        float secondT = (-b + sqrtDiscriminant) / (2.0 * a);
        if (firstT >= 0.0 && firstT <= 1.0) {
            hitT = firstT;
        } else if (secondT >= 0.0 && secondT <= 1.0) {
            hitT = secondT;
        } else {
            return false;
        }

        vec3 hitDelta = startDelta + relativeMotion * hitT;
        float centerDistance = length(hitDelta);
        if (centerDistance > 1.0e-12) {
            normal = -hitDelta / centerDistance;
        }
    }

    reflection = RecordPhotonParticleReflection(
        sourceID,
        targetID,
        normal,
        hitT);
    return true;
}

#endif
"""


def render_color_map() -> str:
    return """// Generated by tools/ExportForceDynamicsSimpleGLSL.py.
// Shared material color-mode mapping for Vulkan particle rendering.

#if defined(DEBUG)
    #extension GL_EXT_debug_printf : enable
#endif
vec3 hsv2rgb(in vec3 hsv);
vec3 colorizeVelocity(float v_ang, float sat, float val);
uint material_color_mode(uint materialID);
vec4 material_color(uint materialID);
uint material_debug_visible(uint materialID);
vec4 material_debug_color(uint materialID);
bool color_map_is_photon(uint index);
vec4 lumens_color(uint index, vec4 baseColor);
vec4 color_from_mode(uint index, uint colorMode, vec4 baseColor);

vec4 color_map(uint index)
{
    uint materialID = uint(round(P[index].material_id));
    if (color_map_is_photon(index))
        return lumens_color(index, material_color(materialID));
    uint colorMode = material_color_mode(materialID);
    vec4 baseColor = material_color(materialID);
    return color_from_mode(index, colorMode, baseColor);

}

bool color_map_is_photon(uint index)
{
    return int(round(P[index].ptype)) == -2;
}

uint material_color_mode(uint materialID)
{
    for (uint ii = 0u; ii < MATERIAL_PROPERTY_COUNT; ++ii)
    {
        if (MATERIAL_PROPERTIES[ii].materialID == materialID)
            return MATERIAL_PROPERTIES[ii].colorMode;
    }

    return COLOR_MODE_COLLISION;
}

vec4 material_color(uint materialID)
{
    for (uint ii = 0u; ii < MATERIAL_PROPERTY_COUNT; ++ii)
    {
        if (MATERIAL_PROPERTIES[ii].materialID == materialID)
            return MATERIAL_PROPERTIES[ii].color;
    }

    return vec4(1.0, 1.0, 1.0, 1.0);
}

uint material_debug_visible(uint materialID)
{
    for (uint ii = 0u; ii < MATERIAL_PROPERTY_COUNT; ++ii)
    {
        if (MATERIAL_PROPERTIES[ii].materialID == materialID)
            return MATERIAL_PROPERTIES[ii].debugVisible;
    }

    return 0u;
}

vec4 material_debug_color(uint materialID)
{
    for (uint ii = 0u; ii < MATERIAL_PROPERTY_COUNT; ++ii)
    {
        if (MATERIAL_PROPERTIES[ii].materialID == materialID)
            return MATERIAL_PROPERTIES[ii].debugColor;
    }

    return vec4(1.0, 1.0, 1.0, 1.0);
}

vec4 lumens_color(uint index, vec4 baseColor)
{
    if (P[index].contactCount == 0u && uint(P[index].colFlg) == 0u)
    {
        uint materialID = uint(round(P[index].material_id));
        if (material_debug_visible(materialID) == 1u)
            return material_debug_color(materialID);
        return vec4(0.0, 0.0, 0.0, 0.0);
    }

    uint materialID = uint(round(P[index].material_id));
    return material_color(materialID);
}

vec4 color_from_mode(uint index, uint colorMode, vec4 baseColor)
{
    if (colorMode == COLOR_MODE_VELOCITY)
    {
        float velocityAngle = ShaderFlags.positionBuffer == 0u
            ? P[index].VelRadA.w
            : P[index].VelRadB.w;
        return vec4(colorizeVelocity(velocityAngle, HSV_SAT, HSV_VAL), baseColor.a);
    }

    if (colorMode == COLOR_MODE_COLLISION)
    {
        if (uint(P[index].colFlg) == 1u)
            return vec4(colcolor, 1.0);
        return vec4(ncolcolor, 1.0);
    }

    if (colorMode == COLOR_MODE_SOLID)
        return baseColor;

    if (colorMode == COLOR_MODE_LUMENS)
        return lumens_color(index, baseColor);

    return vec4(1.0, 1.0, 1.0, 1.0);
}

vec3 hsv2rgb(in vec3 hsv)
{
///H, S and V input range = 0 - 1.0
//R, G and B output range = 0 - 255
    float H = hsv.r;
    float S = hsv.g;
    float V = hsv.b;
    float var_r;
    float var_g;
    float var_b;
    float R = 0;
    float G = 0;
    float B = 0;

    vec3 ret_clr = vec3(0.0);
    if ( S == 0 )
    {
       R = V * 255;
       G = V * 255;
       B = V * 255;
    }
    else
    {
       float var_h = H * 6;
       if ( var_h == 6 ) var_h = 0 ;
       //H must be < 1
       float var_i = int( var_h );             //Or ... var_i = floor( var_h )
       float var_1 = V * ( 1 - S );
       float var_2 = V * ( 1 - S * ( var_h - var_i ) );
       float var_3 = V * ( 1 - S * ( 1 - ( var_h - var_i ) ) );

       if( var_i == 0 )
       {
            var_r = V;
            var_g = var_3 ;
            var_b = var_1;
        }
       else if ( var_i == 1 )
       {
            var_r = var_2 ;
            var_g = V     ;
            var_b = var_1;
        }
       else if ( var_i == 2 )
       {
            var_r = var_1 ;
            var_g = V     ;
            var_b = var_3 ;
        }
       else if ( var_i == 3 )
       {
            var_r = var_1 ;
            var_g = var_2 ;
            var_b = V ;
        }
       else if ( var_i == 4 )
       {
            var_r = var_3 ;
            var_g = var_1 ;
            var_b = V;
        }
       else
       {
            var_r = V     ;
            var_g = var_1 ;
            var_b = var_2 ;
        };

       R = var_r * 255;
       G = var_g * 255;
       B = var_b * 255;
    }
    ret_clr = vec3(R/255,G/255,B/255);
    return ret_clr;
}

vec3 colorizeVelocity(float v_ang, float sat, float val)
{
    float hue = fract(v_ang / 6.28318530718);
    return hsv2rgb(vec3(hue, clamp(sat, 0.0, 1.0), clamp(val, 0.0, 1.0)));
}
"""


def render_fpm() -> str:
    return """// Generated by tools/ExportForceDynamicsSimpleGLSL.py.
// Shared simple source-owned compute schedule.

// Scenarios with richer wall models can define this function before including
// FPM.comp and set EVALUATE_CONFIGURED_WALL_SEGMENT_DEFINED.
#ifndef EVALUATE_CONFIGURED_WALL_SEGMENT_DEFINED
BoundaryWallSegment EvaluateConfiguredWallSegment(uint SourceID, uint BoundaryID)
{
    return EvaluateFunctionWallSegment(SourceID, BoundaryID);
}
#endif

void fpm_comp_main()
{
    uint SourceID = gl_GlobalInvocationID.x;

    if (SourceID == 0u) {
        collOut.numParticles = 0u;
        collOut.CollisionCount = 0u;
        collOut.holdPidx = 0u;
        collOut.vnumParticles = 0u;
        return;
    }

    if (ShaderFlags.StopFlg > 0.0) {
        return;
    }

    if (SourceID >= uint(ShaderFlags.Ptot)) {
        return;
    }

    if (!IsMobileParticleActiveForDynamics(SourceID)) {
        return;
    }

#if defined(DEBUG)
    atomicAdd(collOut.numParticles, 1u);
#endif

    P[SourceID].contactCount = 0u;
    P[SourceID].colFlg = 0u;
    bool photonSource = IsPhotonParticle(SourceID);
    if (photonSource) {
        P[SourceID].material_id = float(PhotonBaseMaterialID());
    }
    vec3 totalForce = vec3(0.0);
    bool photonReflected = false;
    bool photonPositionOverride = false;
    vec3 photonVelocity = GetStartFrameVelocity(SourceID).xyz;
    vec3 photonPosition = GetParticlePosition(SourceID).xyz;

#if defined(FORCE_DYNAMICS_SIMPLE_PISTON_AVAILABLE)
    if (!ProcessPistonCollision(SourceID, totalForce)) {
        return;
    }
#endif

    uint duplicateTargets[DUP_LIST_SIZE];
    uint duplicateCount = 0u;
    uint duplicateWalls[DUP_LIST_SIZE];
    uint duplicateWallCount = 0u;
    bool lightingBallContactProcessed = false;

    for (uint CornerIndex = 0u; CornerIndex < 8u; ++CornerIndex) {
        uint loc = P[SourceID].CornerList[CornerIndex].ploc;
        if (loc == npos) {
            continue;
        }

        for (uint CellSlot = 0u; CellSlot < MAX_CELL_OCCUPANY; ++CellSlot) {
            uint TargetID = clink[loc].idx[CellSlot];
            if (TargetID == 0u) {
                break;
            }
            if (TargetID == SourceID) {
                continue;
            }
            if (TargetID >= uint(ShaderFlags.Ptot)) {
                continue;
            }

            if (IsBoundaryParticle(TargetID)) {
                if (!BoundaryMarkerApplies(SourceID, TargetID)) {
                    continue;
                }

                if (IsLightingBallMarker(TargetID)) {
                    if (!lightingBallContactProcessed) {
                        LightingBallCollisionResult lightingBallResult =
                            ProcessLightingBallCollision(SourceID, totalForce);
                        if (!lightingBallResult.ok) {
                            return;
                        }
                        if (lightingBallResult.handled) {
                            lightingBallContactProcessed = true;
                            if (photonSource) {
                                photonVelocity = ReflectFixedSpeed(
                                    photonVelocity,
                                    lightingBallResult.segment.normal);
                                photonReflected = true;
                                P[SourceID].material_id =
                                    float(LIGHTING_BALL_MATERIAL_ID);
                            }
                        }
                    }
                    continue;
                }

                BoundaryWallSegment segment =
                    EvaluateConfiguredWallSegment(SourceID, TargetID);
                if (!segment.valid) {
                    continue;
                }
                bool duplicateWall = false;
                for (uint duplicateIndex = 0u;
                        duplicateIndex < duplicateWallCount;
                        ++duplicateIndex) {
                    if (duplicateWalls[duplicateIndex] == segment.wallFlag) {
                        duplicateWall = true;
                        break;
                    }
                }
                if (duplicateWall) {
                    continue;
                }
                if (duplicateWallCount >= DUP_LIST_SIZE) {
                    SetError(ERROR_CONTACT_LIST_MISSING, SourceID);
                    return;
                }
                duplicateWalls[duplicateWallCount] = segment.wallFlag;
                duplicateWallCount += 1u;
                if (photonSource) {
                    photonVelocity =
                        ReflectFixedSpeed(photonVelocity, segment.normal);
                    photonReflected = true;
                    P[SourceID].colFlg = 1u;
                    P[SourceID].material_id = P[TargetID].material_id;
                    continue;
                }
                if (!ProcessFunctionWallCollision(
                        SourceID,
                        segment,
                        totalForce)) {
                    return;
                }
                continue;
            }

            if (!IsMobileParticleActiveForDynamics(TargetID)) {
                continue;
            }

            if (ShouldSkipParticlePair(SourceID, TargetID)) {
                continue;
            }

            if (photonSource) {
                PhotonParticleReflection photonReflection;
                if (TryPhotonParticleReflection(
                        SourceID,
                        TargetID,
                        photonReflection)) {
                    photonVelocity = photonReflection.velocity;
                    photonPosition = photonReflection.position;
                    photonReflected = true;
                    photonPositionOverride = true;
                    P[SourceID].colFlg = 1u;
                    P[SourceID].material_id = P[TargetID].material_id;
                    continue;
                }
            }

            bool duplicate = false;
            for (uint duplicateIndex = 0u;
                    duplicateIndex < duplicateCount;
                    ++duplicateIndex) {
                if (duplicateTargets[duplicateIndex] == TargetID) {
                    duplicate = true;
                    break;
                }
            }
            if (duplicate) {
                continue;
            }

            ParticleGeometry geometry =
                GetPhysicalParticleContact(SourceID, TargetID);
            if (!geometry.valid) {
                continue;
            }
            if (photonSource) {
                photonVelocity = ReflectFixedSpeed(photonVelocity, geometry.normal);
                photonReflected = true;
                P[SourceID].colFlg = 1u;
                P[SourceID].material_id = P[TargetID].material_id;
                continue;
            }
            if (duplicateCount >= DUP_LIST_SIZE) {
                SetError(ERROR_CONTACT_LIST_MISSING, SourceID);
                return;
            }
            duplicateTargets[duplicateCount] = TargetID;
            duplicateCount += 1u;
            if (!ProcessParticleCollision(
                    TargetID,
                    SourceID,
                    totalForce,
                    geometry)) {
                return;
            }
        }
    }

    if (!CalcVelocity(SourceID, totalForce)) {
        return;
    }
    if (!ApplySourceMaximumDepth(SourceID, 9401u)) {
        return;
    }
    if (photonReflected) {
        SetNextParticleVelocity(
            SourceID,
            vec4(
                photonVelocity,
                VelocityAngle(photonVelocity.x, photonVelocity.y)));
        if (photonPositionOverride) {
            SetNextParticlePosition(SourceID, photonPosition);
        }
    }

#if defined(FORCE_DYNAMICS_SIMPLE_PISTON_AVAILABLE)
    if (!RegisterResolvedPistonContactStep(SourceID)) {
        return;
    }
#endif

    duplicateCount = 0u;
    duplicateWallCount = 0u;
    bool lightingBallResolvedProcessed = false;

    for (uint CornerIndex = 0u; CornerIndex < 8u; ++CornerIndex) {
        uint loc = P[SourceID].CornerList[CornerIndex].ploc;
        if (loc == npos) {
            continue;
        }

        for (uint CellSlot = 0u; CellSlot < MAX_CELL_OCCUPANY; ++CellSlot) {
            uint TargetID = clink[loc].idx[CellSlot];
            if (TargetID == 0u) {
                break;
            }
            if (TargetID == SourceID) {
                continue;
            }
            if (TargetID >= uint(ShaderFlags.Ptot)) {
                continue;
            }

            if (IsBoundaryParticle(TargetID)) {
                if (!BoundaryMarkerApplies(SourceID, TargetID)) {
                    continue;
                }

                if (IsLightingBallMarker(TargetID)) {
                    if (!lightingBallResolvedProcessed) {
                        if (!RegisterResolvedLightingBallContactStep(SourceID)) {
                            return;
                        }
                        lightingBallResolvedProcessed = true;
                    }
                    continue;
                }

                BoundaryWallSegment segment =
                    EvaluateConfiguredWallSegment(SourceID, TargetID);
                if (!segment.valid) {
                    continue;
                }
                bool duplicateWall = false;
                for (uint duplicateIndex = 0u;
                        duplicateIndex < duplicateWallCount;
                        ++duplicateIndex) {
                    if (duplicateWalls[duplicateIndex] == segment.wallFlag) {
                        duplicateWall = true;
                        break;
                    }
                }
                if (duplicateWall) {
                    continue;
                }
                if (duplicateWallCount >= DUP_LIST_SIZE) {
                    SetError(ERROR_CONTACT_LIST_MISSING, SourceID);
                    return;
                }
                duplicateWalls[duplicateWallCount] = segment.wallFlag;
                duplicateWallCount += 1u;
                if (photonSource) {
                    continue;
                }
                if (!RegisterResolvedFunctionWallContactStep(
                        SourceID,
                        segment)) {
                    return;
                }
                continue;
            }

            if (!IsMobileParticleActiveForDynamics(TargetID)) {
                continue;
            }

            if (ShouldSkipParticlePair(SourceID, TargetID)) {
                continue;
            }
            if (photonSource) {
                continue;
            }

            bool duplicate = false;
            for (uint duplicateIndex = 0u;
                    duplicateIndex < duplicateCount;
                    ++duplicateIndex) {
                if (duplicateTargets[duplicateIndex] == TargetID) {
                    duplicate = true;
                    break;
                }
            }
            if (duplicate) {
                continue;
            }

            ParticleGeometry geometry =
                GetParticleGeometry(SourceID, TargetID);
            if (!geometry.valid) {
                continue;
            }
            if (duplicateCount >= DUP_LIST_SIZE) {
                SetError(ERROR_CONTACT_LIST_MISSING, SourceID);
                return;
            }
            duplicateTargets[duplicateCount] = TargetID;
            duplicateCount += 1u;
            if (!RegisterResolvedParticleContactStep(
                    SourceID,
                    TargetID,
                    geometry)) {
                return;
            }
        }
    }

    if (!ApplySourceMaximumDepth(SourceID, 9402u)) {
        return;
    }
    if (photonReflected) {
        SetNextParticleVelocity(
            SourceID,
            vec4(
                photonVelocity,
                VelocityAngle(photonVelocity.x, photonVelocity.y)));
        if (photonPositionOverride) {
            SetNextParticlePosition(SourceID, photonPosition);
        }
    }

    if (!photonPositionOverride && !CalcPosition(SourceID)) {
        return;
    }
}
"""


def render_compute(source_path: Path, enable_piston: bool = False) -> str:
    piston_include = ""
    if enable_piston:
        piston_include = """#include "piston.glsl"
#define FORCE_DYNAMICS_SIMPLE_PISTON_AVAILABLE
"""
    return f"""#version 460
#extension GL_GOOGLE_include_directive : enable
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

#include "debug.glsl"
#if defined(DEBUG)
    #extension GL_EXT_debug_printf : enable
#endif
#extension GL_KHR_memory_scope_semantics : enable
#extension GL_EXT_shader_atomic_float : enable

#include "params.glsl"
#include "material.glsl"
#include "../common/constants.glsl"
#include "boundary.glsl"
#include "sphere.glsl"
#include "../common/util.glsl"
#include "../common/push.glsl"
#include "../common/atomic.glsl"
#include "../common/CollimageIndex.glsl"
#include "../common/particle.glsl"
#include "../common/photons.glsl"
#include "workgroups.glsl"

{piston_include}\
#include "../common/ForceDynamicsSimple.glsl"
#include "../common/ForceDynamicsSimpleBoundaryParticle.glsl"
#include "../common/ForceDynamicsSimpleFunctionWall.glsl"
#include "../common/ForceDynamicsSimpleRectangleWall.glsl"
#include "../common/ForceDynamicsSimpleLightingBall.glsl"
#if defined(FORCE_DYNAMICS_SIMPLE_PISTON_AVAILABLE)
#include "../common/ForceDynamicsSimplePiston.glsl"
#endif

// Generated from {source_path.as_posix()} by tools/ExportForceDynamicsSimpleGLSL.py.
// Simple source-owned compute schedule.
// Do not hand edit generated dynamics content.

#define EVALUATE_CONFIGURED_WALL_SEGMENT_DEFINED
BoundaryWallSegment EvaluateConfiguredWallSegment(uint SourceID, uint BoundaryID)
{{
    if (RECTANGLE_WALL_SEGMENT_COUNT > 0u) {{
        return EvaluateRectangleWallSegment(SourceID, BoundaryID);
    }}
    return EvaluateFunctionWallSegment(SourceID, BoundaryID);
}}

#include "../common/FPM.comp"

void main()
{{
    fpm_comp_main();
}}
"""


def write_outputs(
    source_path: Path,
    output_dir: Path,
    compute_output: Path,
    visitor: ForceDynamicsVisitor,
    enable_piston: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "photons.glsl").write_text(
        render_photons(),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "color_map.glsl").write_text(
        render_color_map(),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "ForceDynamicsSimple.glsl").write_text(
        render_core(source_path, visitor),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "ForceDynamicsSimpleBoundaryParticle.glsl").write_text(
        render_boundary(source_path, visitor),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "ForceDynamicsSimpleFunctionWall.glsl").write_text(
        render_function_wall(source_path, visitor),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "ForceDynamicsSimpleRectangleWall.glsl").write_text(
        render_rectangle_wall(source_path, visitor),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "ForceDynamicsSimpleLightingBall.glsl").write_text(
        render_lighting_ball(source_path, visitor),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "ForceDynamicsSimplePiston.glsl").write_text(
        render_piston(source_path, visitor),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "FPM.comp").write_text(
        render_fpm(),
        encoding="utf-8",
        newline="\n",
    )
    compute_output.parent.mkdir(parents=True, exist_ok=True)
    compute_output.write_text(
        render_compute(source_path, enable_piston=enable_piston),
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export the simple GenericGenData ForceDynamics GLSL family."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--compute-output", type=Path, default=DEFAULT_COMPUTE_OUTPUT)
    parser.add_argument(
        "--enable-piston",
        action="store_true",
        help="Generate a compute wrapper that includes piston.glsl and enables piston support.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write ForceDynamicsSimple*.glsl. Without this flag, only validate.",
    )
    args = parser.parse_args()

    visitor = parse_source(args.source)
    errors = validate_surface(visitor)
    if errors:
        print("Simple GLSL export surface is not clean:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Simple GLSL export surface is clean.")
    print("Core methods:")
    for method in SIMPLE_CORE_METHODS:
        print(f"  - {method}")
    print("Boundary methods:")
    for method in SIMPLE_BOUNDARY_METHODS:
        print(f"  - {method}")
    print("Function-wall methods:")
    for method in SIMPLE_FUNCTION_WALL_METHODS:
        print(f"  - {method}")
    print("Rectangle/configured-wall methods:")
    for method in SIMPLE_RECTANGLE_WALL_METHODS:
        print(f"  - {method}")
    print("Lighting-ball methods:")
    for method in SIMPLE_LIGHTING_BALL_METHODS:
        print(f"  - {method}")
    print("Piston methods:")
    for method in SIMPLE_PISTON_METHODS:
        print(f"  - {method}")

    if args.write:
        write_outputs(
            args.source,
            args.output_dir,
            args.compute_output,
            visitor,
            enable_piston=args.enable_piston,
        )
        print(f"Wrote simple GLSL family to {args.output_dir}")
        print(f"Wrote simple compute shader to {args.compute_output}")
    else:
        print("Dry run only. Pass --write to generate files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
