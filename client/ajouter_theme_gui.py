import json
import tkinter as tk
from tkinter import filedialog, messagebox

def charger_fichier(label):
    path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if path:
        label.config(text=path)
    return path

def ajouter_theme(gui_path, nouveau_theme_path, nom_theme):
    try:
        with open(gui_path, 'r') as f:
            gui_data = json.load(f)
        with open(nouveau_theme_path, 'r') as f:
            theme_data = json.load(f)

        nouveau_theme = {
            "colours": theme_data.get("defaults", {}).get("colours", {}),
            "button": theme_data.get("button", {}).get("colours", {}),
            "status_bar": {
                "normal_border": theme_data.get("status_bar", {}).get("colours", {}).get("normal_border", "#AAAAAA"),
                "filled_bar": theme_data.get("status_bar", {}).get("colours", {}).get("filled_bar", "#f4251b"),
                "unfilled_bar": theme_data.get("status_bar", {}).get("colours", {}).get("unfilled_bar", "#CCCCCC")
            },
            "label": theme_data.get("label", {}).get("colours", {}),
            "font": theme_data.get("label", {}).get("font", {}),
            "misc": theme_data.get("label", {}).get("misc", {}) | theme_data.get("status_bar", {}).get("misc", {})
        }

        if "themes" not in gui_data:
            gui_data["themes"] = {}

        if nom_theme in gui_data["themes"]:
            if not messagebox.askyesno("Confirmation", f"Le thème '{nom_theme}' existe déjà. Écraser ?"):
                return

        gui_data["themes"][nom_theme] = nouveau_theme

        with open(gui_path, 'w') as f:
            json.dump(gui_data, f, indent=4)

        messagebox.showinfo("Succès", f"Thème '{nom_theme}' ajouté avec succès.")
    except Exception as e:
        messagebox.showerror("Erreur", str(e))

# Interface graphique
root = tk.Tk()
root.title("Ajouter un thème à gui.json")
root.geometry("500x300")
root.resizable(False, False)

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(fill="both", expand=True)

# Chemin gui.json
tk.Label(frame, text="Fichier gui.json :").pack(anchor="w")
gui_label = tk.Label(frame, text="Aucun fichier sélectionné", bg="#eee", anchor="w")
gui_label.pack(fill="x")
tk.Button(frame, text="Parcourir...", command=lambda: charger_fichier(gui_label)).pack()

# Chemin nouveau thème
tk.Label(frame, text="\nFichier du nouveau thème :").pack(anchor="w")
theme_label = tk.Label(frame, text="Aucun fichier sélectionné", bg="#eee", anchor="w")
theme_label.pack(fill="x")
tk.Button(frame, text="Parcourir...", command=lambda: charger_fichier(theme_label)).pack()

# Nom du thème
tk.Label(frame, text="\nNom du thème à ajouter :").pack(anchor="w")
nom_entry = tk.Entry(frame)
nom_entry.pack(fill="x")

# Bouton ajouter
def on_ajouter():
    gui_path = gui_label.cget("text")
    theme_path = theme_label.cget("text")
    nom = nom_entry.get().strip()

    if not all([gui_path.endswith(".json"), theme_path.endswith(".json"), nom]):
        messagebox.showwarning("Champs manquants", "Veuillez sélectionner les fichiers et entrer un nom de thème.")
        return

    ajouter_theme(gui_path, theme_path, nom)

tk.Button(frame, text="Ajouter le thème", bg="#4CAF50", fg="white", command=on_ajouter).pack(pady=15)

root.mainloop()
