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

infinite_health = False
infinite_armor = False
infinite_ammo = False
previous_health = 0
previous_armor = 0

ammo_offsets = {
    "Assault Rifle": 0x140,
    "Submachine Gun": 0x138,
    "Sniper": 0x13C,
    "Shotgun": 0x134,
    "Pistol": 0x12C,
    "Grenade": 0x144,
}


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


def update_ui():
    global infinite_health, infinite_armor, infinite_ammo
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
                pm.write_int(ammo_address, 999999)  # Set ammo to 999999

        time.sleep(0.2)


window = ttk.Window(themename="darkly")
window.title("Assault Cube Trainer")
window.geometry("400x250")
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

threading.Thread(target=update_ui, daemon=True).start()

window.mainloop()
