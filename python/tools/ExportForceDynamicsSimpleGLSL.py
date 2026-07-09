"""Export the clean simple ForceDynamics GLSL family.

This exporter intentionally does not share the legacy exporter surface.  It
targets the GenericGenData/TestPythonBoundarySpheres model:

- active mobile particles
- boundary particles as locality markers
- parametric curve-wall segments
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
    "ParametricBoundaryMarkerApplies",
    "ProcessParametricWallCollision",
    "InitializeParametricWallContactState",
]

SIMPLE_PARAMETRIC_METHODS = [
    "EvaluateParametricWallSegment",
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
        + SIMPLE_PARAMETRIC_METHODS
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
const float MAXIMUM_PENETRATION_FRACTION = 0.5;
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

bool IsMobileParticleActiveForDynamics(uint ParticleID)
{{
    return !IsNullParticle(ParticleID)
        && !IsBoundaryParticle(ParticleID)
        && !IsParticleDead(ParticleID);
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
    collOut.ErrorNumber = errorCode;
    collOut.FrameNumber = uint(ShaderFlags.frameNum);
    return false;
}}

bool SetError(uint errorCode, uint SourceID)
{{
    collOut.ErrorNumber = errorCode;
    collOut.FrameNumber = uint(ShaderFlags.frameNum);
    collOut.ParticleNumber = SourceID;
    return false;
}}

float GetParticleMass(uint ParticleID)
{{
    return max(P[ParticleID].parms.x, EPSILON);
}}

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
    float penetrationReserve =
        (1.0 - MAXIMUM_PENETRATION_FRACTION) * sourceRadius;
    if (inwardDisplacement > penetrationReserve + EPSILON) {{
        return SetError(ERROR_PENETRATION_STEP_TOO_LARGE, SourceID);
    }}
    return true;
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

    float maximumDepth = MAXIMUM_PENETRATION_FRACTION * sourceRadius;
    if (penetrationDepth < maximumDepth - EPSILON) {{
        return true;
    }}

    if (maximumDepthConstraintCount >= MAX_SOURCE_DEPTH_CONSTRAINTS) {{
        return SetError(ERROR_MAX_DEPTH_CONSTRAINT, SourceID);
    }}
    maximumDepthConstraintNormals[maximumDepthConstraintCount] = normal;
    maximumDepthConstraintLimits[maximumDepthConstraintCount] =
        dot(targetVelocity, normal);
    maximumDepthConstraintCount += 1u;
    return true;
}}

bool AccumulateContactForce(
    uint SourceID, ContactForceInput contact, inout vec3 totalForce)
{{
    if (!contact.valid) {{ return true; }}
    float stiffness = GetContactStiffness(
        SourceID, contact.targetID, contact.contactType);
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

bool ProcessParametricWallCollision(
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

bool ProjectSourceVelocityToContactSet(
    vec3 candidateVelocity, out vec3 containedVelocity)
{{
    containedVelocity = candidateVelocity;
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {{
        vec3 normal = maximumDepthConstraintNormals[index];
        float limit = maximumDepthConstraintLimits[index];
        float current = dot(containedVelocity, normal);
        if (current > limit + EPSILON) {{
            containedVelocity -= (current - limit) * normal;
        }}
    }}
    for (uint index = 0u; index < maximumDepthConstraintCount; ++index) {{
        if (dot(containedVelocity, maximumDepthConstraintNormals[index])
                > maximumDepthConstraintLimits[index] + EPSILON) {{
            return false;
        }}
    }}
    return true;
}}

bool ApplySourceMaximumDepth(uint SourceID)
{{
    if (maximumDepthConstraintOwner != SourceID
            || maximumDepthConstraintCount == 0u) {{
        return true;
    }}

    vec4 candidate = GetNextParticleVelocity(SourceID);
    vec3 containedVelocity = vec3(0.0);
    if (!ProjectSourceVelocityToContactSet(
            candidate.xyz, containedVelocity)) {{
        return SetError(ERROR_MAX_DEPTH_CONSTRAINT, SourceID);
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

// Python source: ForceDynamics.py:{line("ParametricBoundaryMarkerApplies")}
bool ParametricBoundaryMarkerApplies(uint SourceID, uint BoundaryID)
{{
    if (!IsBoundaryParticle(BoundaryID)) {{ return false; }}
    vec4 sourcePosition = GetParticlePosition(SourceID);
    vec4 boundaryPosition = GetParticlePosition(BoundaryID);
    return abs(sourcePosition.x - boundaryPosition.x) <= 1.0
        && abs(sourcePosition.y - boundaryPosition.y) <= 1.0
        && abs(sourcePosition.z - boundaryPosition.z) <= 1.0;
}}

bool ProcessParametricWallCollision(
    uint SourceID, BoundaryWallSegment segment, inout vec3 totalForce);

#endif
"""


def render_parametric(source_path: Path, visitor: ForceDynamicsVisitor) -> str:
    line = lambda name: method_line(visitor, name)
    return f"""#ifndef FORCE_DYNAMICS_SIMPLE_PARAMETRIC_WALL_GLSL
#define FORCE_DYNAMICS_SIMPLE_PARAMETRIC_WALL_GLSL

// Generated from {source_path.as_posix()} by tools/ExportForceDynamicsSimpleGLSL.py.
// Parametric curve-wall evaluator for the simple generic model.
// Do not hand edit generated dynamics content.

vec2 ParametricCurvePoint(ParametricCurveSegment segment, float t)
{{
    float t2 = t * t;
    vec4 powers = vec4(1.0, t, t2, t2 * t);
    return vec2(
        dot(segment.xCoefficients, powers),
        dot(segment.yCoefficients, powers));
}}

vec2 ParametricCurveTangent(ParametricCurveSegment segment, float t)
{{
    float t2 = t * t;
    vec4 derivative = vec4(0.0, 1.0, 2.0 * t, 3.0 * t2);
    return vec2(
        dot(segment.xCoefficients, derivative),
        dot(segment.yCoefficients, derivative));
}}

vec2 ParametricCurveSecondDerivative(ParametricCurveSegment segment, float t)
{{
    vec4 derivative = vec4(0.0, 0.0, 2.0, 6.0 * t);
    return vec2(
        dot(segment.xCoefficients, derivative),
        dot(segment.yCoefficients, derivative));
}}

vec3 ParametricCurveClosestPoint(ParametricCurveSegment segment, vec2 point)
{{
    const uint sampleCount = 16u;
    const uint iterationCount = 12u;
    const float solverTolerance = 1.0e-6;
    float bestT = 0.0;
    float bestDistanceSq = 3.402823466e+38;
    uint bestIndex = 0u;

    for (uint index = 0u; index <= sampleCount; ++index) {{
        float t = float(index) / float(sampleCount);
        vec2 delta = ParametricCurvePoint(segment, t) - point;
        float distanceSq = dot(delta, delta);
        if (distanceSq < bestDistanceSq) {{
            bestDistanceSq = distanceSq;
            bestT = t;
            bestIndex = index;
        }}
    }}

    float lower = float((bestIndex > 0u) ? bestIndex - 1u : 0u) / float(sampleCount);
    float upper = float(min(bestIndex + 1u, sampleCount)) / float(sampleCount);
    for (uint iteration = 0u; iteration < iterationCount; ++iteration) {{
        vec2 curvePoint = ParametricCurvePoint(segment, bestT);
        vec2 tangent = ParametricCurveTangent(segment, bestT);
        vec2 secondVector = ParametricCurveSecondDerivative(segment, bestT);
        vec2 delta = curvePoint - point;
        float firstDerivative = dot(delta, tangent);
        float secondDerivative = dot(tangent, tangent) + dot(delta, secondVector);
        if (abs(secondDerivative) <= solverTolerance) {{ break; }}
        float nextT = clamp(bestT - firstDerivative / secondDerivative, lower, upper);
        if (abs(nextT - bestT) <= solverTolerance) {{
            bestT = nextT;
            break;
        }}
        bestT = nextT;
    }}
    return vec3(bestT, ParametricCurvePoint(segment, bestT));
}}

// Python source: ForceDynamics.py:{line("EvaluateParametricWallSegment")}
BoundaryWallSegment EvaluateParametricWallSegment(uint SourceID, uint BoundaryID)
{{
    vec2 marker = GetParticlePosition(BoundaryID).xy;
    ParametricCurveSegment selected = CURVE_WALL_SEGMENTS[0];
    float bestMarkerDistanceSq = 3.402823466e+38;
    for (uint index = 0u; index < CURVE_WALL_SEGMENT_COUNT; ++index) {{
        ParametricCurveSegment candidate = CURVE_WALL_SEGMENTS[index];
        vec3 closest = ParametricCurveClosestPoint(candidate, marker);
        float distanceSq = dot(closest.yz - marker, closest.yz - marker);
        if (distanceSq < bestMarkerDistanceSq) {{
            bestMarkerDistanceSq = distanceSq;
            selected = candidate;
        }}
    }}

    vec3 sourcePosition = GetParticlePosition(SourceID).xyz;
    vec3 closest = ParametricCurveClosestPoint(selected, sourcePosition.xy);
    vec2 wallPoint = closest.yz;
    vec2 tangent = ParametricCurveTangent(selected, closest.x);
    float tangentMagnitude = length(tangent);
    if (tangentMagnitude <= EPSILON) {{
        return BoundaryWallSegment(vec3(0.0), 0.0, 0.0, selected.wallFlag, false);
    }}

    vec3 normal = vec3(tangent.y, -tangent.x, 0.0) / tangentMagnitude;
    float radius = P[SourceID].Data.x;
    float offset = WallContactOffsetDistance(radius);
    vec3 ghost = vec3(wallPoint, sourcePosition.z) + normal * (radius - offset);
    float centerDistance = length(ghost - sourcePosition);
    if (centerDistance >= 2.0 * radius) {{
        return BoundaryWallSegment(normal, 0.0, centerDistance, selected.wallFlag, false);
    }}

    float overlapArea = particle_overlap_area(radius, radius, centerDistance);
    return BoundaryWallSegment(normal, overlapArea, centerDistance, selected.wallFlag, true);
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

#endif

#endif
"""


def render_compute(source_path: Path) -> str:
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
#include "../common/constants.glsl"
#include "boundary.glsl"
#include "../common/util.glsl"
#include "../common/push.glsl"
#include "../common/atomic.glsl"
#include "../common/CollimageIndex.glsl"
#include "../common/particle.glsl"
#include "workgroups.glsl"

#include "../common/ForceDynamicsSimple.glsl"
#include "../common/ForceDynamicsSimpleBoundaryParticle.glsl"
#include "../common/ForceDynamicsSimpleParametricWall.glsl"
#if defined(FORCE_DYNAMICS_SIMPLE_PISTON_AVAILABLE)
#include "../common/ForceDynamicsSimplePiston.glsl"
#endif

// Generated from {source_path.as_posix()} by tools/ExportForceDynamicsSimpleGLSL.py.
// Simple source-owned compute schedule.
// Do not hand edit generated dynamics content.

void main()
{{
    uint SourceID = gl_GlobalInvocationID.x;

    if (SourceID == 0u) {{
        collOut.numParticles = 0u;
        collOut.CollisionCount = 0u;
        collOut.holdPidx = 0u;
        collOut.vnumParticles = 0u;
        return;
    }}

    if (SourceID >= uint(ShaderFlags.Ptot)) {{
        return;
    }}

    if (!IsMobileParticleActiveForDynamics(SourceID)) {{
        return;
    }}

#if defined(DEBUG)
    atomicAdd(collOut.numParticles, 1u);
#endif

    P[SourceID].contactCount = 0u;
    P[SourceID].colFlg = 0u;
    vec3 totalForce = vec3(0.0);

#if defined(FORCE_DYNAMICS_SIMPLE_PISTON_AVAILABLE)
    if (!ProcessPistonCollision(SourceID, totalForce)) {{
        return;
    }}
#endif

    const uint DUP_LIST_SIZE = MAX_CELL_OCCUPANY * 8u;
    uint duplicateTargets[DUP_LIST_SIZE];
    uint duplicateCount = 0u;
    for (uint index = 0u; index < DUP_LIST_SIZE; ++index) {{
        duplicateTargets[index] = 0u;
    }}

    for (uint CornerIndex = 0u; CornerIndex < 8u; ++CornerIndex) {{
        uint loc = P[SourceID].CornerList[CornerIndex].ploc;
        if (loc == npos) {{
            continue;
        }}

        for (uint CellSlot = 0u; CellSlot < MAX_CELL_OCCUPANY; ++CellSlot) {{
            uint TargetID = clink[loc].idx[CellSlot];
            if (TargetID == 0u) {{
                break;
            }}
            if (TargetID == SourceID) {{
                continue;
            }}
            if (TargetID >= uint(ShaderFlags.Ptot)) {{
                continue;
            }}

            if (IsBoundaryParticle(TargetID)) {{
                if (!ParametricBoundaryMarkerApplies(SourceID, TargetID)) {{
                    continue;
                }}

                bool duplicate = false;
                for (uint duplicateIndex = 0u;
                        duplicateIndex < duplicateCount;
                        ++duplicateIndex) {{
                    if (duplicateTargets[duplicateIndex] == TargetID) {{
                        duplicate = true;
                        break;
                    }}
                }}
                if (duplicate) {{
                    continue;
                }}
                if (duplicateCount >= DUP_LIST_SIZE) {{
                    SetError(ERROR_CONTACT_LIST_MISSING, SourceID);
                    return;
                }}
                duplicateTargets[duplicateCount] = TargetID;
                duplicateCount += 1u;

                BoundaryWallSegment segment =
                    EvaluateParametricWallSegment(SourceID, TargetID);
                if (!segment.valid) {{
                    continue;
                }}
                if (!ProcessParametricWallCollision(
                        SourceID,
                        segment,
                        totalForce)) {{
                    return;
                }}
                continue;
            }}

            if (!IsMobileParticleActiveForDynamics(TargetID)) {{
                continue;
            }}

            bool duplicate = false;
            for (uint duplicateIndex = 0u;
                    duplicateIndex < duplicateCount;
                    ++duplicateIndex) {{
                if (duplicateTargets[duplicateIndex] == TargetID) {{
                    duplicate = true;
                    break;
                }}
            }}
            if (duplicate) {{
                continue;
            }}
            if (duplicateCount >= DUP_LIST_SIZE) {{
                SetError(ERROR_CONTACT_LIST_MISSING, SourceID);
                return;
            }}
            duplicateTargets[duplicateCount] = TargetID;
            duplicateCount += 1u;

            ParticleGeometry geometry =
                GetPhysicalParticleContact(SourceID, TargetID);
            if (!geometry.valid) {{
                continue;
            }}
            if (!ProcessParticleCollision(
                    TargetID,
                    SourceID,
                    totalForce,
                    geometry)) {{
                return;
            }}
        }}
    }}

    if (!CalcVelocity(SourceID, totalForce)) {{
        return;
    }}
    if (!ApplySourceMaximumDepth(SourceID)) {{
        return;
    }}
    if (!CalcPosition(SourceID)) {{
        return;
    }}
}}
"""


def write_outputs(
    source_path: Path,
    output_dir: Path,
    compute_output: Path,
    visitor: ForceDynamicsVisitor,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
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
    (output_dir / "ForceDynamicsSimpleParametricWall.glsl").write_text(
        render_parametric(source_path, visitor),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "ForceDynamicsSimplePiston.glsl").write_text(
        render_piston(source_path, visitor),
        encoding="utf-8",
        newline="\n",
    )
    compute_output.parent.mkdir(parents=True, exist_ok=True)
    compute_output.write_text(
        render_compute(source_path),
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
    print("Parametric wall methods:")
    for method in SIMPLE_PARAMETRIC_METHODS:
        print(f"  - {method}")
    print("Piston methods:")
    for method in SIMPLE_PISTON_METHODS:
        print(f"  - {method}")

    if args.write:
        write_outputs(args.source, args.output_dir, args.compute_output, visitor)
        print(f"Wrote simple GLSL family to {args.output_dir}")
        print(f"Wrote simple compute shader to {args.compute_output}")
    else:
        print("Dry run only. Pass --write to generate files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
