import pygame_gui
import json
import os

def load_theme_and_create_manager(active_theme, gui_config_path="gui.json"):
    with open(gui_config_path, 'r') as file:
        config = json.load(file)

    themes = config.get("themes", {})
    if active_theme not in themes:
        raise ValueError(f"Thème '{active_theme}' introuvable.")

    theme = themes[active_theme]

    pygame_gui_theme = {
        "defaults": {
            "colours": {
                "normal_text": theme["colours"]["normal_text"]
            }
        },
        "button": {
            "colours": theme["button"]
        },
        "status_bar": {
            "colours": theme["status_bar"],
            "misc": config.get("misc", {})
        },
        "label": {
            "colours": theme["label"],
            "font": config["font"],
            "misc": config.get("misc", {})
        }
    }

    temp_theme_path = "active_theme.json"
    with open(temp_theme_path, 'w') as temp_file:
        json.dump(pygame_gui_theme, temp_file, indent=4)

    return temp_theme_path