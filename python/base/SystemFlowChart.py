"""Generate the GLSL-shaped system flowchart for the dynamics docs.

This chart describes the algorithm and decisions rather than the Python call
tree.  Nodes link primarily to documentation sections, while the generated PDF
is intended for LaTeX inclusion and the SVG is intended for interactive review.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[2]
DOC_DIR = REPO_DIR / "docs" / "Dynamics"
OUTPUT_DIR = DOC_DIR / "generated"
DOT_FILE = OUTPUT_DIR / "ShadowSystemFlow.dot"

SOURCE_DOC = DOC_DIR / "SourceDocumentation.tex"
PARTICLE_GEOMETRY = DOC_DIR / "ParticleGeometry.tex"
GEO_CONVENTIONS = DOC_DIR / "GeoConventions.tex"
PROGRAMMING_STYLE = DOC_DIR / "ProgrammingStyle.tex"

NODE_DOCS = {
    "Start": (SOURCE_DOC, r"\section{\texttt{ShadowBase:CollisionRun}}"),
    "BeginFrame": (SOURCE_DOC, r"\subsection{Frame Gate}"),
    "ResetFrame": (SOURCE_DOC, r"\subsection{Pre-Contact Hooks and Frame Reset}"),
    "BuildSnapshot": (SOURCE_DOC, r"\section{\texttt{ShadowBase:GeoBuildFrameSnapshot}}"),
    "FrameSnapshotData": (PARTICLE_GEOMETRY, r"\section{Frame Algorithm}"),
    "SourceLoop": (PROGRAMMING_STYLE, r"\subsection{Data-Oriented (Pipeline) Design}"),
    "SourceActive": (SOURCE_DOC, r"\section{\texttt{ShadowBase:GeoDetectContact}}"),
    "TargetLoop": (SOURCE_DOC, r"\subsection{Source-Target Traversal}"),
    "TargetValid": (SOURCE_DOC, r"\subsection{Source-Target Traversal}"),
    "DetectContact": (SOURCE_DOC, r"\section{\texttt{ShadowBase:GeoDetectContact}}"),
    "ContactDecision": (PARTICLE_GEOMETRY, r"\section{Contact Geometry}"),
    "OverlapArea": (PARTICLE_GEOMETRY, r"\section{Circle Overlap Area}"),
    "AddContact": (SOURCE_DOC, r"\subsection{Directed Contact Recording}"),
    "ContactListData": (SOURCE_DOC, r"\subsection{Output}"),
    "HasContacts": (SOURCE_DOC, r"\section{\texttt{ShadowDynamics:GeoPlanContactImpulses}}"),
    "ContactContext": (SOURCE_DOC, r"\section{\texttt{ShadowDynamics:GeoContactContext}}"),
    "ContactLoop": (SOURCE_DOC, r"\subsection{Candidate Construction}"),
    "GeometryValid": (SOURCE_DOC, r"\section{\texttt{ShadowDynamics:GeoParticleGeometry}}"),
    "CalcGeometry": (SOURCE_DOC, r"\section{\texttt{ShadowDynamics:GeoParticleGeometry}}"),
    "CalcWeights": (SOURCE_DOC, r"\subsection{Contact Weights}"),
    "CalcRelVelocity": (PARTICLE_GEOMETRY, r"\section{Relative Normal Velocity}"),
    "CalcRawImpulse": (SOURCE_DOC, r"\subsection{Raw Impulse}"),
    "PhaseDecision": (SOURCE_DOC, r"\subsection{Compression to Rebound Flip}"),
    "Compression": (SOURCE_DOC, r"\subsection{Compression Branch}"),
    "Returning": (SOURCE_DOC, r"\subsection{Returning Branch}"),
    "BuildCandidate": (SOURCE_DOC, r"\subsection{Return Dictionary}"),
    "PairPlan": (SOURCE_DOC, r"\subsection{Pair-Compatible Plan}"),
    "PlanData": (SOURCE_DOC, r"\subsection{Pair-Compatible Plan}"),
    "ResolveContacts": (SOURCE_DOC, r"\subsection{Contact Resolution}"),
    "ReadPlan": (SOURCE_DOC, r"\subsection{Contact Resolution}"),
    "VectorDelta": (PARTICLE_GEOMETRY, r"\section{Current Source-Owned Contact Response}"),
    "WriteSource": (GEO_CONVENTIONS, r"\subsection{No Pairwise Write-Back Shortcut}"),
    "UpdateLedgers": (GEO_CONVENTIONS, r"\subsection{Approved Contact-Owned Internal Momentum Exception}"),
    "MoveParticle": (SOURCE_DOC, r"\subsection{Motion and End Frame}"),
    "EndFrame": (SOURCE_DOC, r"\subsection{Motion and End Frame}"),
}


def section_line(source_file: Path, marker: str) -> int | None:
    for line_number, line in enumerate(
        source_file.read_text(encoding="utf-8-sig").splitlines(),
        start=1,
    ):
        if marker in line:
            return line_number
    return None


def doc_url(node_id: str) -> str | None:
    doc_target = NODE_DOCS.get(node_id)
    if doc_target is None:
        return None
    source_file, marker = doc_target
    line_number = section_line(source_file, marker) or 1
    return f"vscode://file/{source_file.as_posix()}:{line_number}:1"


def dot_node(
    node_id: str,
    label: str,
    shape: str = "box",
    fill: str = "#f8f8f8",
    tooltip: str | None = None,
) -> str:
    url = doc_url(node_id)
    tooltip = tooltip if tooltip is not None else (
        f"Open documentation for {label}" if url else None
    )
    attrs = [
        f'label="{label}"',
        f"shape={shape}",
        f'fillcolor="{fill}"',
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
    action = "#f8f8f8"
    decision = "#fff6d8"
    storage = "#eaf3ff"
    end = "#eaf8ea"

    clusters = [
        dot_cluster(
            "frame_setup",
            "Frame Setup",
            [
                dot_node("Start", "Start Frame", "oval", end),
                dot_node("BeginFrame", "Begin Frame"),
                dot_node("ResetFrame", "Reset Frame State"),
                dot_node("BuildSnapshot", "Build Frame Snapshot"),
                dot_node("FrameSnapshotData", "PosLocFrame / VelRadFrame", "cylinder", storage),
            ],
        ),
        dot_cluster(
            "contact_detection",
            "Contact Detection",
            [
                dot_node("SourceLoop", "For each SourceID", "box", action),
                dot_node("SourceActive", "Source active?", "diamond", decision),
                dot_node("TargetLoop", "For each TargetID", "box", action),
                dot_node("TargetValid", "Target valid and not source?", "diamond", decision),
                dot_node("DetectContact", "Detect particle contact", "box", action),
                dot_node("ContactDecision", "In contact?", "diamond", decision),
                dot_node("OverlapArea", "Compute overlap area", "box", action),
                dot_node("AddContact", "Add directed contact slot", "box", action),
                dot_node("ContactListData", "collision_list / contact slots", "cylinder", storage),
            ],
        ),
        dot_cluster(
            "planning",
            "Impulse Planning",
            [
                dot_node("HasContacts", "Source has contacts?", "diamond", decision),
                dot_node("ContactContext", "Build source contact context", "box", action),
                dot_node("ContactLoop", "For each contact slot", "box", action),
                dot_node("GeometryValid", "Geometry valid?", "diamond", decision),
                dot_node("CalcGeometry", "Calculate contact geometry", "box", action),
                dot_node("CalcWeights", "Calculate source/target weights", "box", action),
                dot_node("CalcRelVelocity", "Calculate relative normal velocity", "box", action),
                dot_node("CalcRawImpulse", "Calculate raw impulse", "box", action),
                dot_node("PhaseDecision", "Compression or returning?", "diamond", decision),
                dot_node("Compression", "Compute compression impulse", "box", action),
                dot_node("Returning", "Compute release impulse", "box", action),
                dot_node("BuildCandidate", "Store directed candidate", "box", action),
                dot_node("PairPlan", "Build pair-compatible plan", "box", action),
                dot_node("PlanData", "GeoPlannedContactImpulses", "cylinder", storage),
            ],
        ),
        dot_cluster(
            "resolution",
            "Source-Owned Resolution",
            [
                dot_node("ResolveContacts", "Resolve contacts for source", "box", action),
                dot_node("ReadPlan", "Read planned impulses", "box", action),
                dot_node("VectorDelta", "Scalar impulse -> vector delta", "box", action),
                dot_node("WriteSource", "Write source velocity only", "box", action),
                dot_node("UpdateLedgers", "Update source-owned ledgers", "box", action),
            ],
        ),
        dot_cluster(
            "motion",
            "Motion",
            [
                dot_node("MoveParticle", "Move source particle", "box", action),
                dot_node("EndFrame", "End Frame", "oval", end),
            ],
        ),
    ]

    edges = [
        dot_edge("Start", "BeginFrame"),
        dot_edge("BeginFrame", "ResetFrame"),
        dot_edge("ResetFrame", "BuildSnapshot"),
        dot_edge("BuildSnapshot", "FrameSnapshotData", "write"),
        dot_edge("FrameSnapshotData", "SourceLoop", "snapshot ready"),
        dot_edge("SourceLoop", "SourceActive"),
        dot_edge("SourceActive", "TargetLoop", "yes"),
        dot_edge("SourceActive", "MoveParticle", "no"),
        dot_edge("TargetLoop", "TargetValid"),
        dot_edge("TargetValid", "DetectContact", "yes"),
        dot_edge("TargetValid", "TargetLoop", "no / next target"),
        dot_edge("DetectContact", "ContactDecision"),
        dot_edge("ContactDecision", "OverlapArea", "yes"),
        dot_edge("ContactDecision", "TargetLoop", "no / next target"),
        dot_edge("OverlapArea", "AddContact"),
        dot_edge("AddContact", "ContactListData", "write"),
        dot_edge("ContactListData", "TargetLoop", "next target"),
        dot_edge("TargetLoop", "HasContacts", "target scan done"),
        dot_edge("HasContacts", "MoveParticle", "no"),
        dot_edge("HasContacts", "ContactContext", "yes"),
        dot_edge("ContactContext", "ContactLoop"),
        dot_edge("ContactLoop", "CalcGeometry"),
        dot_edge("CalcGeometry", "GeometryValid"),
        dot_edge("GeometryValid", "ContactLoop", "no / next contact"),
        dot_edge("GeometryValid", "CalcWeights", "yes"),
        dot_edge("CalcWeights", "CalcRelVelocity"),
        dot_edge("CalcRelVelocity", "CalcRawImpulse"),
        dot_edge("CalcRawImpulse", "PhaseDecision"),
        dot_edge("PhaseDecision", "Compression", "compression"),
        dot_edge("PhaseDecision", "Returning", "returning"),
        dot_edge("Compression", "BuildCandidate"),
        dot_edge("Returning", "BuildCandidate"),
        dot_edge("BuildCandidate", "ContactLoop", "next contact"),
        dot_edge("ContactLoop", "PairPlan", "contact scan done"),
        dot_edge("PairPlan", "PlanData", "write"),
        dot_edge("PlanData", "ResolveContacts"),
        dot_edge("ResolveContacts", "ReadPlan"),
        dot_edge("ReadPlan", "VectorDelta"),
        dot_edge("VectorDelta", "WriteSource"),
        dot_edge("WriteSource", "UpdateLedgers"),
        dot_edge("UpdateLedgers", "MoveParticle"),
        dot_edge("MoveParticle", "SourceLoop", "next source"),
        dot_edge("SourceLoop", "EndFrame", "all sources done"),
    ]

    lines = [
        "digraph ShadowSystemFlow {",
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
