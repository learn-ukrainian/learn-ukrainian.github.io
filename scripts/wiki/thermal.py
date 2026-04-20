"""Minimal macOS thermal-state helper for MLX backoff control."""

from __future__ import annotations

import ctypes


def nsprocessinfo_thermal_state() -> int:
    """Return NSProcessInfo thermalState (0-3), defaulting to Nominal on failure."""

    try:
        ctypes.CDLL("/System/Library/Frameworks/Foundation.framework/Foundation")
        objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        process_info_class = objc.objc_getClass(b"NSProcessInfo")
        process_info_sel = objc.sel_registerName(b"processInfo")
        thermal_state_sel = objc.sel_registerName(b"thermalState")
        if not process_info_class or not process_info_sel or not thermal_state_sel:
            return 0

        objc.objc_msgSend.restype = ctypes.c_void_p
        process_info = objc.objc_msgSend(process_info_class, process_info_sel)
        if not process_info:
            return 0

        objc.objc_msgSend.restype = ctypes.c_long
        thermal_state = int(objc.objc_msgSend(process_info, thermal_state_sel))
        return thermal_state if 0 <= thermal_state <= 3 else 0
    except Exception:
        return 0
