
"""Binary particle record shared by Python data generators and Vulkan.

This module defines the on-disk particle record written to ``*.bin`` files by
the Python generators and read by the Vulkan particle loader. The field order,
field type, and total size are part of the binary file format. Keep this
structure in sync with ``vulkan/src/VulkanObj/pdata.hpp``.

The first record in generated motion files is usually a null particle with
``pnum == 0``. Vulkan keeps particle index 0 reserved because zero is also used
as an empty/end marker in cell occupancy lists.
"""

import ctypes


PTYPE_NULL = -1.0
PTYPE_MOBILE = 0.0
BOUNDARY_EVALUATOR_NONE = PTYPE_MOBILE
BOUNDARY_EVALUATOR_HORIZONTAL = 1.0
BOUNDARY_EVALUATOR_VERTICAL = 2.0
BOUNDARY_EVALUATOR_CD_NOZZLE = 3.0
BOUNDARY_EVALUATOR_LINEAR = 4.0
BOUNDARY_EVALUATOR_FUNCTION_WALL = 5.0

BOUNDARY_EVALUATOR_IDS = {
    "horizontal_wall": BOUNDARY_EVALUATOR_HORIZONTAL,
    "vertical_wall": BOUNDARY_EVALUATOR_VERTICAL,
    "cd_nozzle_wall": BOUNDARY_EVALUATOR_CD_NOZZLE,
    "linear_wall": BOUNDARY_EVALUATOR_LINEAR,
    "function_wall": BOUNDARY_EVALUATOR_FUNCTION_WALL,
}


class pdata(ctypes.Structure):
    """Packed particle input record.

    All fields are stored as C doubles for compatibility with the existing C++
    ``pdata`` struct. Vulkan converts this compact input record into its larger
    runtime ``Particle``/SSBO representation:

    - ``rx``, ``ry``, ``rz`` become ``PosLocA.xyz`` and ``PosLocB.xyz``.
    - ``vx``, ``vy``, ``vz`` become ``VelRad.xyz``.
    - ``radius`` becomes ``Data.x``.
    - ``collision_stiffness_q`` becomes ``Data.y``.
    - ``ptype == -1`` identifies the reserved null particle at index zero.
    - ``ptype == 0`` identifies a mobile particle. Positive ``ptype`` values
      identify boundary markers. Generic function-wall simulations use
      ``ptype == 1`` for all boundary markers; the simulation wall model and
      ``curve_wall_segments`` determine how those markers are evaluated.
    - ``material_id`` identifies the material/species used for rendering and
      heterogeneous dynamics. It is independent of boundary classification and
      wall-evaluator dispatch.
    - ``state_flg`` becomes ``Data.w``.
    - ``molar_mass`` becomes ``parms.x``.

    ``state_flg`` lifecycle values are copied to runtime ``Data.w``:

    - ``Data.w < 0`` = dead or retired; ignored by dynamics and rendering.
    - ``Data.w == 0`` = active from frame zero.
    - ``Data.w > 0`` = pending release frame; active when
      ``frameNum >= Data.w``.

    Boundary markers use ``ptype`` for classification. Their ``state_flg`` is
    normally ``0`` and must not be used for wall identity or evaluator
    dispatch.

    Do not reorder or rename fields without changing the matching Vulkan
    ``pdata.hpp`` struct and regenerating any binary files that use the old
    layout.
    """

    _fields_ = [
        ("pnum", ctypes.c_double),        # Particle id. Zero is reserved for the null particle.
        ("rx", ctypes.c_double),          # Initial x position.
        ("ry", ctypes.c_double),          # Initial y position.
        ("rz", ctypes.c_double),          # Initial z position.
        ("radius", ctypes.c_double),      # Particle radius.
        ("vx", ctypes.c_double),          # Initial x velocity.
        ("vy", ctypes.c_double),          # Initial y velocity.
        ("vz", ctypes.c_double),          # Initial z velocity.
        ("ptype", ctypes.c_double),       # 0 mobile; positive values identify boundary markers.
        ("state_flg", ctypes.c_double),   # Runtime lifecycle copied to Data.w.
        ("molar_mass", ctypes.c_double),  # Particle mass; copied to Vulkan parms.x.
        ("material_id", ctypes.c_double),    # Material/species id; independent of boundary dispatch.
        ("collision_stiffness_q", ctypes.c_double),  # Particle-owned collision stiffness; copied to Data.y.
        ]
        
