import pymem
import pymem.process
import struct
import json
import time

# ── Wczytaj lokalny plik offsets ─────────────────────────────────────────────
with open("offsets.json") as f:
    offsets = json.load(f)
with open("client_dll.json") as f:
    client = json.load(f)

classes = client["client.dll"]["classes"]

# Offsety z pliku który wkleiłeś
OFF_LOCAL_PLAYER  = offsets["client.dll"]["dwLocalPlayerPawn"]
OFF_POS           = classes["C_BasePlayerPawn"]["fields"]["m_vOldOrigin"]      # 5512
OFF_YAW           = classes["C_CSPlayerPawn"]["fields"]["m_angEyeAngles"]      # 15824

OFF_HEALTH     = classes["C_BaseEntity"]["fields"]["m_iHealth"]        # 852
OFF_LIFESTATE  = classes["C_BaseEntity"]["fields"]["m_lifeState"]

# ── Podłącz do procesu ────────────────────────────────────────────────────────
pm   = pymem.Pymem("cs2.exe")
base = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll

def read_float(addr):
    return struct.unpack("f", pm.read_bytes(addr, 4))[0]


def get_player_data():
    raw = pm.read_longlong(base + OFF_LOCAL_PLAYER)

    # W CS2 dwLocalPlayerPawn to już bezpośredni ptr do CCSPlayerPawn
    # ale czasem trzeba odjąć 1 lub użyć innego odczytu
    pawn = raw

    x = read_float(pawn + OFF_POS)
    y = read_float(pawn + OFF_POS + 4)
    z = read_float(pawn + OFF_POS + 8)

    pitch = read_float(pawn + OFF_YAW)      # góra/dół
    yaw   = read_float(pawn + OFF_YAW + 4)  # lewo/prawo

    return {"pos": (x, y, z), "pitch": pitch, "yaw": yaw}

def is_player_alive():
    pawn = pm.read_longlong(base + OFF_LOCAL_PLAYER)
    if pawn < 0x10000000:
        return False
    health = pm.read_int(pawn + OFF_HEALTH)
    return health > 0

# if __name__ == "__main__":
#     while True:
#         try:
#             d = get_player_data()
#             print(f"X={d['pos'][0]:.1f} Y={d['pos'][1]:.1f} Z={d['pos'][2]:.1f} | pitch={d['pitch']:.1f}° yaw={d['yaw']:.1f}°")
#         except Exception as e:
#             print(f"Błąd: {e}")
#         time.sleep(0.016)