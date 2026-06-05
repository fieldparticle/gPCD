"""Generate a proposed simplified GLSL-shaped system flowchart.

This diagram is intentionally not linked.  It is a design proposal used to make
the desired staged algorithm easier to see before refactoring code toward it.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[2]
DOC_DIR = REPO_DIR / "docs" / "Dynamics"
OUTPUT_DIR = DOC_DIR / "generated"
DOT_FILE = OUTPUT_DIR / "ShadowProposedSystemFlow.dot"


def dot_node(node_id: str, label: str, shape: str = "box", fill: str = "#f8f8f8") -> str:
    return f'    {node_id} [label="{label}", shape={shape}, fillcolor="{fill}"];'


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
            "frame",
            "Frame Inputs",
            [
                dot_node("Start", "Start Frame", "oval", end),
                dot_node("Snapshot", "Build frame snapshot", "box", action),
                dot_node("SnapshotData", "snapshot positions / velocities", "cylinder", storage),
            ],
        ),
        dot_cluster(
            "detect",
            "Pass 1: Detect and Store Geometry",
            [
                dot_node("DetectLoop", "source-target scan", "box", action),
                dot_node("Contact", "contact?", "diamond", decision),
                dot_node("StoreGeometry", "store directed contact geometry", "box", action),
                dot_node("ContactData", "contact slots: target, normal, area, distance", "cylinder", storage),
            ],
        ),
        dot_cluster(
            "context",
            "Pass 2: Build Source Context",
            [
                dot_node("SourceContextLoop", "for each source contact list", "box", action),
                dot_node("HasContacts", "has contacts?", "diamond", decision),
                dot_node("BuildContext", "sum overlap and closing momentum", "box", action),
                dot_node("ContextData", "source context: total area, available momentum", "cylinder", storage),
            ],
        ),
        dot_cluster(
            "allocation",
            "Pass 3: Plan Source Allocation",
            [
                dot_node("AllocationLoop", "for each source contact list", "box", action),
                dot_node("SourceTarget", "compute source-level target", "box", action),
                dot_node("Distribute", "distribute target by contact weights", "box", action),
                dot_node("CandidateData", "directed candidates", "cylinder", storage),
            ],
        ),
        dot_cluster(
            "pair_plan",
            "Pass 4: Pair Compatibility",
            [
                dot_node("PairLoop", "for each unordered pair", "box", action),
                dot_node("PairCompatible", "choose compatible pair impulse", "box", action),
                dot_node("PlanData", "planned directed impulses", "cylinder", storage),
            ],
        ),
        dot_cluster(
            "apply",
            "Pass 5: Apply Source-Owned Writes",
            [
                dot_node("ApplyLoop", "for each source", "box", action),
                dot_node("ReadPlan", "read planned impulses", "box", action),
                dot_node("VectorSum", "sum vector impulse delta", "box", action),
                dot_node("WriteSource", "write source velocity only", "box", action),
                dot_node("UpdateLedgers", "update source-owned ledgers", "box", action),
            ],
        ),
        dot_cluster(
            "move",
            "Pass 6: Move",
            [
                dot_node("Move", "move particles", "box", action),
                dot_node("End", "End Frame", "oval", end),
            ],
        ),
    ]

    edges = [
        dot_edge("Start", "Snapshot"),
        dot_edge("Snapshot", "SnapshotData", "write"),
        dot_edge("SnapshotData", "DetectLoop", "read"),
        dot_edge("DetectLoop", "Contact"),
        dot_edge("Contact", "StoreGeometry", "yes"),
        dot_edge("Contact", "DetectLoop", "no / next pair"),
        dot_edge("StoreGeometry", "ContactData", "write"),
        dot_edge("ContactData", "DetectLoop", "next pair"),
        dot_edge("DetectLoop", "SourceContextLoop", "scan done"),
        dot_edge("SourceContextLoop", "HasContacts"),
        dot_edge("HasContacts", "BuildContext", "yes"),
        dot_edge("HasContacts", "SourceContextLoop", "no / next source"),
        dot_edge("BuildContext", "ContextData", "write"),
        dot_edge("ContextData", "SourceContextLoop", "next source"),
        dot_edge("SourceContextLoop", "AllocationLoop", "contexts done"),
        dot_edge("AllocationLoop", "SourceTarget"),
        dot_edge("SourceTarget", "Distribute"),
        dot_edge("Distribute", "CandidateData", "write"),
        dot_edge("CandidateData", "AllocationLoop", "next source"),
        dot_edge("AllocationLoop", "PairLoop", "allocation done"),
        dot_edge("PairLoop", "PairCompatible"),
        dot_edge("PairCompatible", "PlanData", "write"),
        dot_edge("PlanData", "PairLoop", "next pair"),
        dot_edge("PairLoop", "ApplyLoop", "plan done"),
        dot_edge("ApplyLoop", "ReadPlan"),
        dot_edge("ReadPlan", "VectorSum"),
        dot_edge("VectorSum", "WriteSource"),
        dot_edge("WriteSource", "UpdateLedgers"),
        dot_edge("UpdateLedgers", "ApplyLoop", "next source"),
        dot_edge("ApplyLoop", "Move", "all sources done"),
        dot_edge("Move", "End"),
    ]

    lines = [
        "digraph ShadowProposedSystemFlow {",
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
