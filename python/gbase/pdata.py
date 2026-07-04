
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

BOUNDARY_EVALUATOR_IDS = {
    "horizontal_wall": BOUNDARY_EVALUATOR_HORIZONTAL,
    "vertical_wall": BOUNDARY_EVALUATOR_VERTICAL,
    "cd_nozzle_wall": BOUNDARY_EVALUATOR_CD_NOZZLE,
    "linear_wall": BOUNDARY_EVALUATOR_LINEAR,
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
      identify boundary markers and also select their wall evaluator:
      horizontal is 1, vertical is 2, CD nozzle is 3, and linear converging
      nozzle is 4. Vulkan copies a
      boundary marker's ``ptype`` into runtime ``Data.z``.
    - ``temp_vel`` is independent reserved particle data. It is not used for
      boundary classification or wall-evaluator dispatch.
    - ``state_flg`` becomes ``Data.w``.
    - ``molar_mass`` becomes ``parms.x``.

    ``state_flg`` lifecycle values match ``base.SimCalc``:

    - ``0`` = reservoir/inactive, waiting to be released.
    - ``1`` = active, moved and considered for collisions.
    - ``2`` = escaped, removed from active simulation and not reused.
    - ``3`` = retained, removed from active motion but kept/stored.

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
        ("ptype", ctypes.c_double),       # 0 mobile; positive values identify the boundary evaluator.
        ("state_flg", ctypes.c_double),   # Lifecycle: 0 reservoir, 1 active, 2 escaped, 3 retained.
        ("molar_mass", ctypes.c_double),  # Particle mass; copied to Vulkan parms.x.
        ("temp_vel", ctypes.c_double),    # Reserved particle data; independent of boundary dispatch.
        ("collision_stiffness_q", ctypes.c_double),  # Particle-owned collision stiffness; copied to Data.y.
        ]
        
