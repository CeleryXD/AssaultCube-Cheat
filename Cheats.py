import math
import threading
import time

import pymem
import ttkbootstrap as ttk
from pymem.process import module_from_name
from ttkbootstrap.constants import *

try:
    pm = pymem.Pymem("ac_client.exe")
    game_module = module_from_name(pm.process_handle, "ac_client.exe").lpBaseOfDll
except pymem.exception.ProcessNotFound as e:
    print("Could not find process: Game not open or installed")
    exit()
except Exception as e:
    print(f"Unexpected error: {e}")
    exit()

# Control flags
infinite_health = False
infinite_armor = False
infinite_ammo = False
aimbot_enabled = False
esp_enabled = False
previous_health = 0
previous_armor = 0

# Ammo offsets
ammo_offsets = {
    "Assault Rifle": 0x140,
    "Submachine Gun": 0x138,
    "Sniper": 0x13C,
    "Shotgun": 0x134,
    "Pistol": 0x12C,
    "Grenade": 0x144,
}

# Enemy-related offsets
enemy_list_offset = 0x18AC04  # Adjust based on your findings
enemy_count_offset = 0x18AC0C  # Adjust based on your findings
enemy_position_offset = [0x2C, 0x30, 0x28]  # X, Y, Z offsets


def get_ptr_addr(base, offsets):
    addr = pm.read_int(base)
    for offset in offsets[:-1]:
        addr = pm.read_int(addr + offset)
    return addr + offsets[-1]


def get_current_health_and_armor():
    global previous_health, previous_armor
    health_address = get_ptr_addr(game_module + 0x0017E0A8, [0xEC])
    armor_address = get_ptr_addr(game_module + 0x0017E0A8, [0xF0])

    previous_health = pm.read_int(health_address)
    previous_armor = pm.read_int(armor_address)


def aim_at(target_pos):
    local_player_ptr = get_ptr_addr(game_module + 0x0017E0A8, [])
    player_camera_x = get_ptr_addr(local_player_ptr, [0x34])
    player_camera_y = get_ptr_addr(local_player_ptr, [0x38])

    local_player_pos = [
        pm.read_float(player_camera_x),
        pm.read_float(player_camera_y),
        pm.read_float(get_ptr_addr(local_player_ptr, [0x28])),  # Z position
    ]

    delta_x = target_pos[0] - local_player_pos[0]
    delta_y = target_pos[1] - local_player_pos[1]

    angle_x = -math.atan2(delta_y, delta_x) * (180 / math.pi)
    angle_y = math.atan2(
        target_pos[2] - local_player_pos[2], math.sqrt(delta_x**2 + delta_y**2)
    ) * (180 / math.pi)

    pm.write_float(local_player_ptr + 0x34, angle_x)  # Camera X offset
    pm.write_float(local_player_ptr + 0x38, angle_y)  # Camera Y offset


def update_ui():
    global infinite_health, infinite_armor, infinite_ammo, aimbot_enabled, esp_enabled
    while True:
        if infinite_health:
            health_address = get_ptr_addr(game_module + 0x0017E0A8, [0xEC])
            pm.write_int(health_address, 9999)

        if infinite_armor:
            armor_address = get_ptr_addr(game_module + 0x0017E0A8, [0xF0])
            pm.write_int(armor_address, 9999)

        if infinite_ammo:
            for weapon, offset in ammo_offsets.items():
                ammo_address = get_ptr_addr(game_module + 0x0017E0A8, [offset])
                pm.write_int(ammo_address, 999999)

        if aimbot_enabled:
            enemy_count = pm.read_int(
                get_ptr_addr(game_module + enemy_count_offset, [])
            )
            closest_distance = float("inf")
            best_target = None

            for i in range(enemy_count):
                enemy_address = pm.read_int(
                    get_ptr_addr(game_module + enemy_list_offset, [i * 0x4])
                )  # Adjust based on your structure
                enemy_pos = [
                    pm.read_float(get_ptr_addr(enemy_address, enemy_position_offset)),
                    pm.read_float(
                        get_ptr_addr(enemy_address, enemy_position_offset + [1])
                    ),
                    pm.read_float(
                        get_ptr_addr(enemy_address, enemy_position_offset + [2])
                    ),
                ]

                if esp_enabled:
                    print(f"Enemy #{i}: Position: {enemy_pos}")

                # Aim at the closest enemy
                distance = math.sqrt(
                    (enemy_pos[0] - local_player_pos[0]) ** 2
                    + (enemy_pos[1] - local_player_pos[1]) ** 2
                )
                if distance < closest_distance:
                    closest_distance = distance
                    best_target = enemy_pos

            if best_target:
                aim_at(best_target)

        time.sleep(0.2)


# Window
window = ttk.Window(themename="darkly")
window.title("Assault Cube Trainer")
window.geometry("400x300")
window.resizable(False, False)

title_label = ttk.Label(window, text="Assault Cube Trainer", font=("Helvetica", 16))
title_label.grid(row=0, column=0, padx=10, pady=10)


def toggle_health():
    global infinite_health
    if not infinite_health:
        get_current_health_and_armor()
    else:
        health_address = get_ptr_addr(game_module + 0x0017E0A8, [0xEC])
        pm.write_int(health_address, previous_health)
    infinite_health = not infinite_health


def toggle_armor():
    global infinite_armor
    if not infinite_armor:
        get_current_health_and_armor()
    else:
        armor_address = get_ptr_addr(game_module + 0x0017E0A8, [0xF0])
        pm.write_int(armor_address, previous_armor)
    infinite_armor = not infinite_armor


def toggle_infinite_ammo():
    global infinite_ammo
    infinite_ammo = not infinite_ammo


def toggle_aimbot():
    global aimbot_enabled
    aimbot_enabled = not aimbot_enabled


def toggle_esp():
    global esp_enabled
    esp_enabled = not esp_enabled


health_checkbox = ttk.Checkbutton(
    window,
    text="Infinite Health",
    variable=ttk.BooleanVar(value=infinite_health),
    command=toggle_health,
    bootstyle="primary-square-toggle",
)
health_checkbox.grid(row=1, column=0, padx=10, pady=5, sticky="w")

armor_checkbox = ttk.Checkbutton(
    window,
    text="Infinite Armor",
    variable=ttk.BooleanVar(value=infinite_armor),
    command=toggle_armor,
    bootstyle="primary-square-toggle",
)
armor_checkbox.grid(row=2, column=0, padx=10, pady=5, sticky="w")

ammo_checkbox = ttk.Checkbutton(
    window,
    text="Infinite Ammo",
    variable=ttk.BooleanVar(value=infinite_ammo),
    command=toggle_infinite_ammo,
    bootstyle="primary-square-toggle",
)
ammo_checkbox.grid(row=3, column=0, padx=10, pady=5, sticky="w")

aimbot_checkbox = ttk.Checkbutton(
    window,
    text="Aimbot",
    variable=ttk.BooleanVar(value=aimbot_enabled),
    command=toggle_aimbot,
    bootstyle="primary-square-toggle",
)
aimbot_checkbox.grid(row=4, column=0, padx=10, pady=5, sticky="w")

esp_checkbox = ttk.Checkbutton(
    window,
    text="ESP",
    variable=ttk.BooleanVar(value=esp_enabled),
    command=toggle_esp,
    bootstyle="primary-square-toggle",
)
esp_checkbox.grid(row=5, column=0, padx=10, pady=5, sticky="w")

threading.Thread(target=update_ui, daemon=True).start()

window.mainloop()
