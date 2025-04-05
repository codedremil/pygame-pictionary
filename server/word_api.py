'''
Gestion des mots issus d'un dictionnaire distant
'''
from random import choice
import requests

mots_deja_devinés = []
dictionary = [
    "Chien","Chat", "Éléphant", "Lion", "Giraf", "Kangourou", "Pingouin", "Ours", "Renard", "Tortue",
    "Plage", "Montagne", "Forêt", "Désert", "Ville", "Parc", "Lac", "Île", "Château", "École",
    "Voiture", "Téléphone", "Ordinateur", "Livre", "Chaise", "Table", "Lampe", "Montre", "Vélo", "Guitare",
    "Courir", "Danser", "Nager", "Sauter", "Manger", "Dormir", "Lire", "Écrire", "Chanter", "Jouer",
    "Superman", "Cléopâtre", "Harry Potter", "Cendrillon", "Spiderman", "Batman", "Blanche-Neige", "Iron Man", "Le Petit Prince", "Alice",
    "Pomme", "Banane", "Carotte", "Fromage", "Pizza", "Gâteau", "Hamburger", "Glace", "Chocolat", "Pâtes",
   "Médecin", "Pompier", "Policier", "Professeur", "Cuisinier", "Artiste", "Astronaute", "Pilote", "Musicien", "Infirmière",
    "Football", "Basketball", "Tennis", "Natation", "Cyclisme", "Athlétisme", "Ski", "Rugby", "Golf", "Équitation",
   "Joie", "Tristesse", "Colère", "Surprise", "Peur", "Amour", "Bonheur", "Étonnement", "Fatigue", "Ennui",
    "Arc-en-ciel", "Étoile", "Soleil", "Lune", "Nuage", "Pluie", "Feu", "Montgolfière", "Bateau", "Avion"
]

# dictionnaire 2 avec des catégories
dico_v2 = pictionary_words = {
    "Animaux": ["Chien", "Chat", "Éléphant", "Lion", "Giraf", "Kangourou", "Pingouin", "Ours", "Renard", "Tortue"],
    "Lieux": ["Plage", "Montagne", "Forêt", "Désert", "Ville", "Parc", "Lac", "Île", "Château", "École"],
    "Objets": ["Voiture", "Téléphone", "Ordinateur", "Livre", "Chaise", "Table", "Lampe", "Montre", "Vélo", "Guitare"],
    "Actions": ["Courir", "Danser", "Nager", "Sauter", "Manger", "Dormir", "Lire", "Écrire", "Chanter", "Jouer"],
    "Personnages": ["Superman", "Cléopâtre", "Harry Potter", "Cendrillon", "Spiderman", "Batman", "Blanche-Neige", "Iron Man", "Le Petit Prince", "Alice"],
    "Aliments": ["Pomme", "Banane", "Carotte", "Fromage", "Pizza", "Gâteau", "Hamburger", "Glace", "Chocolat", "Pâtes"],
    "Métiers": ["Médecin", "Pompier", "Policier", "Professeur", "Cuisinier", "Artiste", "Astronaute", "Pilote", "Musicien", "Infirmière"],
    "Sports": ["Football", "Basketball", "Tennis", "Natation", "Cyclisme", "Athlétisme", "Ski", "Rugby", "Golf", "Équitation"],
    "Émotions": ["Joie", "Tristesse", "Colère", "Surprise", "Peur", "Amour", "Bonheur", "Étonnement", "Fatigue", "Ennui"],
    "Divers": ["Arc-en-ciel", "Étoile", "Soleil", "Lune", "Nuage", "Pluie", "Feu", "Montgolfière", "Bateau", "Avion"]
}



def get_local_word():
    mot_choisi_local = choice(dictionary)
    
    
    while mot_choisi_local in mots_deja_devinés:
        mot_choisi_local = choice(dictionary)
        
    

    mots_deja_devinés.append(mot_choisi_local)

    return mot_choisi_local



def get_word():
    try:
        url = "https://random-words-api.vercel.app/word/french"
        resp = requests.get(url)
        if resp.ok:
            #print(resp.text)
            doc = resp.json()
            #print(doc)
            word = doc[0]['word']
            mots_deja_devinés.append(word) 
            return word

        return get_local_word()
    except Exception as e:
        return get_local_word()

if __name__ == '__main__':
    print(get_word())
  
