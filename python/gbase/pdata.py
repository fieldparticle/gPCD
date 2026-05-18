
import ctypes
import math
class pdata(ctypes.Structure):
    _fields_ = [
        ("pnum", ctypes.c_double),
        ("rx", ctypes.c_double),
        ("ry", ctypes.c_double),
        ("rz", ctypes.c_double),
        ("radius", ctypes.c_double),
        ("vx", ctypes.c_double),
        ("vy", ctypes.c_double),
        ("vz", ctypes.c_double),
        ("ptype", ctypes.c_double),
        ("state_flg", ctypes.c_double),
        ("molar_mass", ctypes.c_double),
        ("temp_vel", ctypes.c_double),
        ]
        