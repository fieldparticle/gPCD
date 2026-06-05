"""Generate the current ShadowLinDynamics function flowchart.

This chart shows only the flow inside ShadowLinDynamics.py.  At this stage the
contact-dynamics path is intentionally a single linear chain with one loop over
the source particle's contact list.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[2]
DOC_DIR = REPO_DIR / "docs" / "Dynamics"
OUTPUT_DIR = DOC_DIR / "generated"
DOT_FILE = OUTPUT_DIR / "ShadowLinFlow.dot"

SHADOW_LIN_DYNAMICS = REPO_DIR / "python" / "base" / "ShadowLinDynamics.py"
SOURCE_DOCUMENTATION = DOC_DIR / "SourceDocumentation.tex"

NODE_SOURCES = {
    "ContactDynamics": SHADOW_LIN_DYNAMICS,
    "BeginSourceContactParms": SHADOW_LIN_DYNAMICS,
    "InitializeContactState": SHADOW_LIN_DYNAMICS,
    "GetContactState": SHADOW_LIN_DYNAMICS,
    "GetParticleGeometry": SHADOW_LIN_DYNAMICS,
    "GetParticlePosition": SHADOW_LIN_DYNAMICS,
    "AppendContactSlot": SHADOW_LIN_DYNAMICS,
    "GetContactSlots": SHADOW_LIN_DYNAMICS,
    "GetCollisionPhase": SHADOW_LIN_DYNAMICS,
    "GetCollisionInternalMomentum": SHADOW_LIN_DYNAMICS,
    "CalculateContactParms": SHADOW_LIN_DYNAMICS,
    "GetStartFrameVelocity": SHADOW_LIN_DYNAMICS,
    "GetReducedMass": SHADOW_LIN_DYNAMICS,
    "CalculateContactWeights": SHADOW_LIN_DYNAMICS,
    "CalculateContactImpulses": SHADOW_LIN_DYNAMICS,
    "GetPairStiffness": SHADOW_LIN_DYNAMICS,
    "ApplySourceVelocityDelta": SHADOW_LIN_DYNAMICS,
    "GetParticleMass": SHADOW_LIN_DYNAMICS,
    "UpdateContactLedgers": SHADOW_LIN_DYNAMICS,
    "SetCollisionInternalMomentum": SHADOW_LIN_DYNAMICS,
    "SetCollisionPhase": SHADOW_LIN_DYNAMICS,
    "SyncInternalMomentum": SHADOW_LIN_DYNAMICS,
    "GetInternalMomentum": SHADOW_LIN_DYNAMICS,
    "SetInternalMomentum": SHADOW_LIN_DYNAMICS,
}


def node_url(node_id: str) -> str | None:
    if node_id not in NODE_SOURCES:
        return None
    section_text = f"\\section{{ShadowLinDynamics:{node_id}}}"
    for line_number, line in enumerate(
        SOURCE_DOCUMENTATION.read_text(encoding="utf-8-sig").splitlines(),
        start=1,
    ):
        if line.strip() == section_text:
            return f"vscode://file/{SOURCE_DOCUMENTATION.as_posix()}:{line_number}:1"
    return f"vscode://file/{SOURCE_DOCUMENTATION.as_posix()}:1:1"


def dot_node(
    node_id: str,
    label: str,
    shape: str = "box",
    fill: str = "#f8f8f8",
) -> str:
    url = node_url(node_id)
    attrs = [
        f'label="{label}"',
        f"shape={shape}",
        f'fillcolor="{fill}"',
    ]
    if url:
        attrs.extend(
            [
                f'URL="{url}"',
                f'tooltip="Open the {label} section in SourceDocumentation.tex"',
                'target="_blank"',
            ]
        )
    return f"    {node_id} [{', '.join(attrs)}];"


def dot_edge(source: str, target: str, label: str | None = None) -> str:
    if label:
        return f'    {source} -> {target} [label="{label}"];'
    return f"    {source} -> {target};"


def build_dot() -> str:
    action = "#f8f8f8"

    edges = [
        dot_edge("ContactDynamics", "BeginSourceContactParms"),
        dot_edge("BeginSourceContactParms", "InitializeContactState", "first contact"),
        dot_edge("InitializeContactState", "GetContactState"),
        dot_edge("GetContactState", "AppendContactSlot"),
        dot_edge("AppendContactSlot", "GetContactSlots"),
        dot_edge("GetContactSlots", "GetCollisionPhase"),
        dot_edge("GetCollisionPhase", "GetCollisionInternalMomentum"),
        dot_edge("GetCollisionInternalMomentum", "GetParticleGeometry"),
        dot_edge("GetParticleGeometry", "GetParticlePosition"),
        dot_edge("GetParticlePosition", "GetStartFrameVelocity"),
        dot_edge("GetStartFrameVelocity", "GetReducedMass"),
        dot_edge("GetReducedMass", "CalculateContactParms"),
        dot_edge("CalculateContactParms", "InitializeContactState", "next contact"),
        dot_edge("CalculateContactParms", "CalculateContactWeights", "all contacts done"),
        dot_edge("CalculateContactWeights", "CalculateContactImpulses"),
        dot_edge("CalculateContactImpulses", "GetPairStiffness"),
        dot_edge("GetPairStiffness", "CalculateContactImpulses"),
        dot_edge("CalculateContactImpulses", "ApplySourceVelocityDelta"),
        dot_edge("ApplySourceVelocityDelta", "GetParticleMass"),
        dot_edge("GetParticleMass", "ApplySourceVelocityDelta"),
        dot_edge("ApplySourceVelocityDelta", "UpdateContactLedgers"),
        dot_edge("UpdateContactLedgers", "SetCollisionInternalMomentum"),
        dot_edge("SetCollisionInternalMomentum", "SetCollisionPhase"),
        dot_edge("SetCollisionPhase", "SyncInternalMomentum"),
        dot_edge("SyncInternalMomentum", "GetInternalMomentum"),
        dot_edge("GetInternalMomentum", "SetInternalMomentum"),
    ]

    lines = [
        "digraph ShadowLinFlow {",
        "  graph [",
        "    rankdir=TB,",
        "    compound=true,",
        "    bgcolor=\"white\",",
        "    fontname=\"Consolas\",",
        "    fontsize=11,",
        "    splines=ortho,",
        "    nodesep=0.75,",
        "    ranksep=0.65",
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
        "    color=\"#505050\",",
        "    arrowsize=0.7",
        "  ];",
        "",
    ]
    lines.extend(
        [
            dot_node("ContactDynamics", "ContactDynamics", "box", action),
            dot_node("BeginSourceContactParms", "BeginSourceContactParms", "box", action),
            dot_node("InitializeContactState", "InitializeContactState", "box", action),
            dot_node("GetContactState", "GetContactState", "box", action),
            dot_node("GetParticleGeometry", "GetParticleGeometry", "box", action),
            dot_node("GetParticlePosition", "GetParticlePosition", "box", action),
            dot_node("AppendContactSlot", "AppendContactSlot", "box", action),
            dot_node("GetContactSlots", "GetContactSlots", "box", action),
            dot_node("GetCollisionPhase", "GetCollisionPhase", "box", action),
            dot_node("GetCollisionInternalMomentum", "GetCollisionInternalMomentum", "box", action),
            dot_node("CalculateContactParms", "CalculateContactParms", "box", action),
            dot_node("GetStartFrameVelocity", "GetStartFrameVelocity", "box", action),
            dot_node("GetReducedMass", "GetReducedMass", "box", action),
            dot_node("CalculateContactWeights", "CalculateContactWeights", "box", action),
            dot_node("CalculateContactImpulses", "CalculateContactImpulses", "box", action),
            dot_node("GetPairStiffness", "GetPairStiffness", "box", action),
            dot_node("ApplySourceVelocityDelta", "ApplySourceVelocityDelta", "box", action),
            dot_node("GetParticleMass", "GetParticleMass", "box", action),
            dot_node("UpdateContactLedgers", "UpdateContactLedgers", "box", action),
            dot_node("SetCollisionInternalMomentum", "SetCollisionInternalMomentum", "box", action),
            dot_node("SetCollisionPhase", "SetCollisionPhase", "box", action),
            dot_node("SyncInternalMomentum", "SyncInternalMomentum", "box", action),
            dot_node("GetInternalMomentum", "GetInternalMomentum", "box", action),
            dot_node("SetInternalMomentum", "SetInternalMomentum", "box", action),
        ]
    )
    lines.extend(
        [
            "",
            "  {",
            "    rank=same;",
            "    ContactDynamics;",
            "    CalculateContactWeights;",
            "  }",
        ]
    )
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
