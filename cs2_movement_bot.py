import ctypes

# ── Win32 raw mouse input (works inside game windows) ─────────────────────────

def raw_mouse_move(dx, dy):
    """
    Sends a relative mouse movement using the Win32 SendInput API.
    This bypasses the cursor and works even when the game captures the mouse.
    """
    MOUSEEVENTF_MOVE = 0x0001

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx",          ctypes.c_long),
            ("dy",          ctypes.c_long),
            ("mouseData",   ctypes.c_ulong),
            ("dwFlags",     ctypes.c_ulong),
            ("time",        ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            class _MOUSEINPUT(ctypes.Structure):
                _fields_ = MOUSEINPUT._fields_
            _fields_ = [("mi", MOUSEINPUT)]
        _anonymous_ = ("_input",)
        _fields_ = [("type", ctypes.c_ulong), ("_input", _INPUT)]

    inp = INPUT()
    inp.type = 0  # INPUT_MOUSE
    inp.mi.dx = dx
    inp.mi.dy = dy
    inp.mi.mouseData = 0
    inp.mi.dwFlags = MOUSEEVENTF_MOVE
    inp.mi.time = 0
    inp.mi.dwExtraInfo = None

    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

