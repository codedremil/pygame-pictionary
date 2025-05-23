import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
import os

def charger_fichier(label):
    path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if path:
        label.config(text=path)
    return path

def charger_gui_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def enregistrer_gui_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def lister_themes(gui_path):
    data = charger_gui_json(gui_path)
    return list(data.get("themes", {}).keys())

def ajouter_theme_par_fichier():
    gui_path = gui_label_file.cget("text")
    theme_path = theme_file_label.cget("text")
    theme_name = theme_name_entry.get().strip()

    if not all([gui_path.endswith(".json"), theme_path.endswith(".json"), theme_name]):
        messagebox.showerror("Erreur", "Veuillez remplir tous les champs.")
        return

    try:
        gui_data = charger_gui_json(gui_path)
        with open(theme_path, 'r') as f:
            theme_data = json.load(f)

        new_theme = {
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

        gui_data.setdefault("themes", {})[theme_name] = new_theme
        enregistrer_gui_json(gui_path, gui_data)
        messagebox.showinfo("Succès", f"Thème '{theme_name}' ajouté avec succès.")
        maj_liste_themes()
    except Exception as e:
        messagebox.showerror("Erreur", str(e))


def choisir_couleur(var, bouton):
    couleur = colorchooser.askcolor()[1]
    if couleur:
        var.set(couleur)
        bouton.config(bg=couleur, text=couleur)

def creer_theme_complet():
    gui_path = gui_label_form.cget("text")
    theme_name = simple_name_entry.get().strip()
    if not theme_name or not gui_path.endswith(".json"):
        messagebox.showerror("Erreur", "Remplir tous les champs.")
        return

    new_theme = {
        "colours": {
            "normal_text": couleurs["normal_text"].get()
        },
        "button": {
            "normal_border": couleurs["button_border"].get(),
            "normal_bg": couleurs["button_bg"].get(),
            "normal_text": couleurs["button_text"].get()
        },
        "status_bar": {
            "normal_border": couleurs["bar_border"].get(),
            "filled_bar": couleurs["bar_filled"].get(),
            "unfilled_bar": couleurs["bar_unfilled"].get()
        },
        "label": {
            "dark_bg": couleurs["label_bg"].get(),
            "normal_text": couleurs["normal_text"].get(),
            "text_shadow": couleurs["label_shadow"].get()
        },
        "font": {
            "name": font_name_entry.get(),
            "size": font_size_entry.get(),
            "bold": "0",
            "italic": "0"
        },
        "misc": {
            "text_shadow": "1" if shadow_var.get() else "0",
            "text_shadow_size": shadow_size_entry.get(),
            "text_shadow_offset": shadow_offset_entry.get(),
            "follow_sprite_offset": sprite_offset_entry.get(),
            "border_width": border_width_entry.get()
        }
    }

    gui_data = charger_gui_json(gui_path)
    gui_data.setdefault("themes", {})[theme_name] = new_theme
    enregistrer_gui_json(gui_path, gui_data)
    messagebox.showinfo("Succès", f"Thème '{theme_name}' créé.")
    maj_liste_themes()

def supprimer_theme():
    gui_path = gui_label_delete.cget("text")
    theme = theme_to_delete.get()

    if not gui_path.endswith(".json") or not theme:
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier et un thème.")
        return

    gui_data = charger_gui_json(gui_path)
    if theme in gui_data.get("themes", {}):
        confirm = messagebox.askyesno("Confirmer la suppression", f"Supprimer le thème '{theme}' ?")
        if confirm:
            del gui_data["themes"][theme]
            enregistrer_gui_json(gui_path, gui_data)
            messagebox.showinfo("Thème supprimé", f"Le thème '{theme}' a été supprimé.")
            maj_liste_themes()

def maj_liste_themes():
    if gui_label_delete.cget("text").endswith(".json"):
        themes = lister_themes(gui_label_delete.cget("text"))
        theme_menu["menu"].delete(0, "end")
        for t in themes:
            theme_menu["menu"].add_command(label=t, command=tk._setit(theme_to_delete, t))
        if themes:
            theme_to_delete.set(themes[0])
        else:
            theme_to_delete.set("")

# --- GUI ---
root = tk.Tk()
root.title("Gestionnaire de thèmes GUI")
root.geometry("600x600")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

# === Onglet 1 : Ajout depuis fichier ===
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="Ajouter depuis fichier")

tk.Label(tab1, text="Fichier gui.json :").pack(anchor="w")
gui_label_file = tk.Label(tab1, text="Aucun fichier", bg="#eee", anchor="w")
gui_label_file.pack(fill="x")
tk.Button(tab1, text="Parcourir", command=lambda: charger_fichier(gui_label_file)).pack()

tk.Label(tab1, text="\nFichier du thème à ajouter :").pack(anchor="w")
theme_file_label = tk.Label(tab1, text="Aucun fichier", bg="#eee", anchor="w")
theme_file_label.pack(fill="x")
tk.Button(tab1, text="Parcourir", command=lambda: charger_fichier(theme_file_label)).pack()

tk.Label(tab1, text="\nNom du thème :").pack(anchor="w")
theme_name_entry = tk.Entry(tab1)
theme_name_entry.pack(fill="x")

tk.Button(tab1, text="Ajouter thème", bg="#4CAF50", fg="white", command=ajouter_theme_par_fichier).pack(pady=10)

# Onglet 2 : Création manuelle avec scroll
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="Créer manuellement")

# Canvas + Scrollbar
canvas = tk.Canvas(tab2, borderwidth=0, background="#f5f5f5")
scroll_y = tk.Scrollbar(tab2, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, background="#f5f5f5")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scroll_y.set)

canvas.pack(side="left", fill="both", expand=True)
scroll_y.pack(side="right", fill="y")

# === Contenu dans scrollable_frame ===
tk.Label(scrollable_frame, text="Fichier gui.json :").pack(anchor="w")
gui_label_form = tk.Label(scrollable_frame, text="Aucun fichier", bg="#eee", anchor="w")
gui_label_form.pack(fill="x")
tk.Button(scrollable_frame, text="Parcourir", command=lambda: charger_fichier(gui_label_form)).pack()

tk.Label(scrollable_frame, text="\nNom du nouveau thème :").pack(anchor="w")
simple_name_entry = tk.Entry(scrollable_frame)
simple_name_entry.pack(fill="x")

couleurs = {}
boutons = {}

champs_couleur = {
    "normal_text": "Texte normal",
    "button_border": "Bouton - bordure",
    "button_bg": "Bouton - fond",
    "button_text": "Bouton - texte",
    "bar_border": "Barre - bordure",
    "bar_filled": "Barre - remplie",
    "bar_unfilled": "Barre - vide",
    "label_bg": "Label - fond",
    "label_shadow": "Ombre du texte"
}

for cle, label in champs_couleur.items():
    tk.Label(scrollable_frame, text=label + " :").pack(anchor="w")
    couleurs[cle] = tk.StringVar(value="#CCCCCC")
    boutons[cle] = tk.Button(scrollable_frame, text="#CCCCCC", bg="#CCCCCC",
                             command=lambda c=cle: choisir_couleur(couleurs[c], boutons[c]))
    boutons[cle].pack(fill="x")

tk.Label(scrollable_frame, text="\nPolice :").pack(anchor="w")
font_name_entry = tk.Entry(scrollable_frame)
font_name_entry.insert(0, "montserrat")
font_name_entry.pack(fill="x")

tk.Label(scrollable_frame, text="Taille :").pack(anchor="w")
font_size_entry = tk.Entry(scrollable_frame)
font_size_entry.insert(0, "12")
font_size_entry.pack(fill="x")

# Section misc
tk.Label(scrollable_frame, text="\nEffets visuels (misc) :").pack(anchor="w")

shadow_var = tk.IntVar(value=1)
tk.Checkbutton(scrollable_frame, text="Activer ombre du texte", variable=shadow_var).pack(anchor="w")

tk.Label(scrollable_frame, text="Taille de l'ombre :").pack(anchor="w")
shadow_size_entry = tk.Entry(scrollable_frame)
shadow_size_entry.insert(0, "1")
shadow_size_entry.pack(fill="x")

tk.Label(scrollable_frame, text="Décalage de l'ombre (x,y) :").pack(anchor="w")
shadow_offset_entry = tk.Entry(scrollable_frame)
shadow_offset_entry.insert(0, "1,1")
shadow_offset_entry.pack(fill="x")

tk.Label(scrollable_frame, text="Décalage sprite (x,y) :").pack(anchor="w")
sprite_offset_entry = tk.Entry(scrollable_frame)
sprite_offset_entry.insert(0, "-5, 32")
sprite_offset_entry.pack(fill="x")

tk.Label(scrollable_frame, text="Largeur bordure :").pack(anchor="w")
border_width_entry = tk.Entry(scrollable_frame)
border_width_entry.insert(0, "1")
border_width_entry.pack(fill="x")

tk.Button(scrollable_frame, text="Créer le thème", bg="#2196F3", fg="white", command=creer_theme_complet).pack(pady=10)

# === Onglet 3 : Supprimer un thème ===
tab3 = ttk.Frame(notebook)
notebook.add(tab3, text="Supprimer un thème")

tk.Label(tab3, text="Fichier gui.json :").pack(anchor="w")
gui_label_delete = tk.Label(tab3, text="Aucun fichier", bg="#eee", anchor="w")
gui_label_delete.pack(fill="x")
tk.Button(tab3, text="Parcourir", command=lambda: [charger_fichier(gui_label_delete), maj_liste_themes()]).pack()

tk.Label(tab3, text="\nSélectionne un thème à supprimer :").pack(anchor="w")
theme_to_delete = tk.StringVar()
theme_menu = tk.OptionMenu(tab3, theme_to_delete, "")
theme_menu.pack(fill="x")

tk.Button(tab3, text="Supprimer", bg="#f44336", fg="white", command=supprimer_theme).pack(pady=10)

root.mainloop()
