"""Generate the source-flow Graphviz diagrams for the dynamics docs.

The script writes a readable DOT file and, when Graphviz `dot` is available,
renders SVG and PNG outputs.  It does not depend on the Python graphviz package;
the only external renderer is the Graphviz command-line executable.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[2]
DOC_DIR = REPO_DIR / "docs" / "Dynamics"
OUTPUT_DIR = DOC_DIR / "generated"
DOT_FILE = OUTPUT_DIR / "ShadowSourceFlow.dot"

SHADOW_BASE = REPO_DIR / "python" / "base" / "ShadowBase.py"
SHADOW_DYNAMICS = REPO_DIR / "python" / "base" / "ShadowDynamics.py"
GEO_RUNNER = REPO_DIR / "python" / "GeoRunner.py"
REPORTING = REPO_DIR / "python" / "base" / "Reporting.py"

NODE_SOURCES = {
    "CollisionRun": SHADOW_BASE,
    "GeoBeginFrame": SHADOW_BASE,
    "GeoApplyBeforeContactScanHook": SHADOW_BASE,
    "GeoResetFrameState": SHADOW_BASE,
    "GeoApplyStartRunHook": SHADOW_BASE,
    "GeoBuildFrameSnapshot": SHADOW_BASE,
    "GeoRecordFrameStartDiagnostics": SHADOW_BASE,
    "GeoDetectContact": SHADOW_BASE,
    "isParticleContact": SHADOW_BASE,
    "GeoAddParticleContact": SHADOW_DYNAMICS,
    "GeoBuildWallContactLists": SHADOW_BASE,
    "GeoPlanContactImpulses": SHADOW_DYNAMICS,
    "GeoContactContext": SHADOW_DYNAMICS,
    "GeoCalculatePairContact": SHADOW_DYNAMICS,
    "GeoParticleGeometry": SHADOW_DYNAMICS,
    "GeoStartFrameVelocity": SHADOW_DYNAMICS,
    "GeoVelocityProgressImpulse": SHADOW_DYNAMICS,
    "GeoBuildPairCompatiblePlan": SHADOW_DYNAMICS,
    "GeoResolveContacts": SHADOW_BASE,
    "GeoProcessCollisions": SHADOW_DYNAMICS,
    "GeoRecordAfterResolveDiagnostics": SHADOW_BASE,
    "GeoMoveParticles": SHADOW_BASE,
    "GeoEndFrame": SHADOW_BASE,
    "particle_position": SHADOW_BASE,
    "particle_overlap_area": SHADOW_BASE,
    "GeoVelocityAngle": SHADOW_BASE,
    "_report_particles": GEO_RUNNER,
    "report_frame_momentum": REPORTING,
    "report_contacts": REPORTING,
    "report_particle": REPORTING,
}


def function_line(source_file: Path, function_name: str) -> int | None:
    for line_number, line in enumerate(
        source_file.read_text(encoding="utf-8-sig").splitlines(),
        start=1,
    ):
        if line.lstrip().startswith(f"def {function_name}("):
            return line_number
    return None


def vscode_url(source_file: Path, function_name: str) -> str:
    line_number = function_line(source_file, function_name) or 1
    return f"vscode://file/{source_file.as_posix()}:{line_number}:1"


def node_url(node_id: str) -> str | None:
    source_file = NODE_SOURCES.get(node_id)
    if source_file is None:
        return None
    return vscode_url(source_file, node_id)


def dot_node(
    node_id: str,
    label: str,
    shape: str = "box",
    url: str | None = None,
    tooltip: str | None = None,
) -> str:
    url = url if url is not None else node_url(node_id)
    tooltip = tooltip if tooltip is not None else (
        f"Open {label} in VS Code" if url else None
    )
    attrs = [
        f'label="{label}"',
        f"shape={shape}",
    ]
    if url:
        attrs.extend(
            [
                f'URL="{url}"',
                f'tooltip="{tooltip}"',
                'target="_blank"',
            ]
        )
    return f"    {node_id} [{', '.join(attrs)}];"


def dot_edge(source: str, target: str, label: str | None = None) -> str:
    if label:
        return f'    {source} -> {target} [label="{label}"];'
    return f"    {source} -> {target};"


def dot_cluster(cluster_id: str, label: str, node_lines: list[str]) -> str:
    lines = [
        f"  subgraph cluster_{cluster_id} {{",
        f'    label="{label}";',
        "    color=\"#c8c8c8\";",
        "    style=\"rounded\";",
    ]
    lines.extend(node_lines)
    lines.append("  }")
    return "\n".join(lines)


def build_dot() -> str:
    clusters = [
        dot_cluster(
            "setup",
            "Frame Setup",
            [
                dot_node("CollisionRun", "CollisionRun", "oval"),
                dot_node("GeoBeginFrame", "GeoBeginFrame"),
                dot_node("GeoApplyBeforeContactScanHook", "GeoApplyBeforeContactScanHook"),
                dot_node("GeoResetFrameState", "GeoResetFrameState"),
                dot_node("GeoApplyStartRunHook", "GeoApplyStartRunHook"),
                dot_node("GeoBuildFrameSnapshot", "GeoBuildFrameSnapshot"),
                dot_node("GeoRecordFrameStartDiagnostics", "GeoRecordFrameStartDiagnostics"),
            ],
        ),
        dot_cluster(
            "detect",
            "Contact Detection",
            [
                dot_node("GeoDetectContact", "GeoDetectContact"),
                dot_node("isParticleContact", "isParticleContact"),
                dot_node("GeoAddParticleContact", "GeoAddParticleContact"),
            ],
        ),
        dot_cluster(
            "planning",
            "Impulse Planning",
            [
                dot_node("GeoPlanContactImpulses", "GeoPlanContactImpulses"),
                dot_node("GeoContactContext", "GeoContactContext"),
                dot_node("GeoCalculatePairContact", "GeoCalculatePairContact"),
                dot_node("GeoParticleGeometry", "GeoParticleGeometry"),
                dot_node("GeoStartFrameVelocity", "GeoStartFrameVelocity"),
                dot_node("GeoVelocityProgressImpulse", "GeoVelocityProgressImpulse"),
                dot_node("GeoBuildPairCompatiblePlan", "GeoBuildPairCompatiblePlan"),
                dot_node("GeoPlannedContactImpulses", "GeoPlannedContactImpulses", "note"),
            ],
        ),
        dot_cluster(
            "resolve",
            "Contact Resolution",
            [
                dot_node("GeoResolveContacts", "GeoResolveContacts"),
                dot_node("GeoProcessCollisions", "GeoProcessCollisions"),
                dot_node("GeoRecordAfterResolveDiagnostics", "GeoRecordAfterResolveDiagnostics"),
            ],
        ),
        dot_cluster(
            "motion",
            "Motion / End Frame",
            [
                dot_node("GeoMoveParticles", "GeoMoveParticles"),
                dot_node("GeoEndFrame", "GeoEndFrame"),
            ],
        ),
        dot_cluster(
            "capture",
            "Capture / Reporting",
            [
                dot_node("_report_particles", "_report_particles"),
                dot_node("report_frame_momentum", "Reporting.report_frame_momentum"),
                dot_node("report_contacts", "Reporting.report_contacts"),
                dot_node("report_particle", "Reporting.report_particle"),
                dot_node("CaptureCSV", "momentum / contacts / particle CSV", "note"),
            ],
        ),
        dot_cluster(
            "common",
            "Shared Helpers",
            [
                dot_node("particle_position", "particle_position"),
                dot_node("particle_overlap_area", "particle_overlap_area"),
                dot_node("GeoVelocityAngle", "GeoVelocityAngle"),
            ],
        ),
    ]

    edges = [
        dot_edge("CollisionRun", "GeoBeginFrame"),
        dot_edge("GeoBeginFrame", "GeoApplyBeforeContactScanHook"),
        dot_edge("GeoApplyBeforeContactScanHook", "GeoResetFrameState"),
        dot_edge("GeoResetFrameState", "GeoApplyStartRunHook"),
        dot_edge("GeoApplyStartRunHook", "GeoBuildFrameSnapshot"),
        dot_edge("GeoBuildFrameSnapshot", "GeoRecordFrameStartDiagnostics"),
        dot_edge("GeoRecordFrameStartDiagnostics", "GeoDetectContact"),
        dot_edge("GeoDetectContact", "GeoPlanContactImpulses"),
        dot_edge("GeoPlanContactImpulses", "GeoResolveContacts"),
        dot_edge("GeoResolveContacts", "GeoRecordAfterResolveDiagnostics"),
        dot_edge("GeoRecordAfterResolveDiagnostics", "GeoMoveParticles"),
        dot_edge("GeoMoveParticles", "GeoEndFrame"),
        dot_edge("GeoDetectContact", "isParticleContact", "detect"),
        dot_edge("isParticleContact", "particle_position", "position"),
        dot_edge("isParticleContact", "particle_overlap_area", "area"),
        dot_edge("GeoDetectContact", "GeoAddParticleContact", "record"),
        dot_edge("GeoPlanContactImpulses", "GeoContactContext", "source context"),
        dot_edge("GeoPlanContactImpulses", "GeoCalculatePairContact", "per contact"),
        dot_edge("GeoCalculatePairContact", "GeoParticleGeometry", "geometry"),
        dot_edge("GeoParticleGeometry", "particle_position", "position"),
        dot_edge("GeoParticleGeometry", "particle_overlap_area", "area"),
        dot_edge("GeoCalculatePairContact", "GeoStartFrameVelocity", "snapshot velocity"),
        dot_edge("GeoCalculatePairContact", "GeoVelocityProgressImpulse", "phase/impulse"),
        dot_edge("GeoPlanContactImpulses", "GeoBuildPairCompatiblePlan", "pair reconcile"),
        dot_edge("GeoBuildPairCompatiblePlan", "GeoPlannedContactImpulses", "store plan"),
        dot_edge("GeoResolveContacts", "GeoProcessCollisions", "per source"),
        dot_edge("GeoProcessCollisions", "GeoPlannedContactImpulses", "read plan"),
        dot_edge("GeoProcessCollisions", "GeoVelocityAngle", "VelRad.w"),
        dot_edge("CollisionRun", "_report_particles", "frame result"),
        dot_edge("_report_particles", "report_frame_momentum", "momentum.csv"),
        dot_edge("_report_particles", "report_contacts", "contacts.csv"),
        dot_edge("_report_particles", "report_particle", "pN.csv"),
        dot_edge("report_frame_momentum", "CaptureCSV"),
        dot_edge("report_contacts", "CaptureCSV"),
        dot_edge("report_particle", "CaptureCSV"),
    ]

    lines = [
        "digraph ShadowSourceFlow {",
        "  graph [",
        "    rankdir=TB,",
        "    compound=true,",
        "    bgcolor=\"white\",",
        "    fontname=\"Consolas\",",
        "    fontsize=11",
        "  ];",
        "  node [",
        "    fontname=\"Consolas\",",
        "    fontsize=10,",
        "    style=\"rounded,filled\",",
        "    fillcolor=\"#f8f8f8\",",
        "    color=\"#606060\"",
        "  ];",
        "  edge [",
        "    fontname=\"Consolas\",",
        "    fontsize=9,",
        "    color=\"#505050\"",
        "  ];",
        "",
    ]
    lines.extend(clusters)
    lines.append("")
    lines.extend(edges)
    lines.append("}")
    return "\n".join(lines) + "\n"


def render(dot_file: Path, output_format: str) -> Path | None:
    dot_exe = shutil.which("dot")
    if dot_exe is None:
        return None

    output_file = dot_file.with_suffix(f".{output_format}")
    subprocess.run(
        [dot_exe, f"-T{output_format}", str(dot_file), "-o", str(output_file)],
        check=True,
    )
    return output_file


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOT_FILE.write_text(build_dot(), encoding="utf-8")
    print(f"wrote {DOT_FILE}")

    for output_format in ("svg", "pdf", "png"):
        output_file = render(DOT_FILE, output_format)
        if output_file is None:
            print("Graphviz dot not found; skipped rendering")
            break
        print(f"wrote {output_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
