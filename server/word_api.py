'''
Gestion des mots issus d'un dictionnaire distant
'''
from random import choice
import requests


dictionary = [
    "chat", "chien", "maison", "voiture", "soleil", "lune", "montagne", "rivière", "arbre", "fleur",
    "livre", "stylo", "chaise", "table", "ordinateur", "portable", "télévision", "lampe", "fenêtre", "porte",
    "ballon", "vélo", "train", "avion", "bateau", "camion", "moto", "bus", "métro", "fusée",
    "couteau", "fourchette", "cuillère", "assiette", "verre", "bouteille", "casserole", "poêle", "micro-onde", "frigo",
    "pomme", "banane", "fraise", "orange", "raisin", "citron", "tomate", "carotte", "pomme de terre", "brocoli",
    "poulet", "pizza", "hamburger", "fromage", "pain", "beurre", "oeuf", "gâteau", "bonbon", "glace",
    "éléphant", "tigre", "lion", "zèbre", "girafe", "singe", "ours", "renard", "loup", "lapin",
    "cheval", "vache", "mouton", "cochon", "poule", "canard", "poisson", "requin", "dauphin", "baleine",
    "sirène", "dragon", "fantôme", "zombie", "vampire", "sorcière", "magicien", "pirate", "chevalier", "prince",
    "princesse", "roi", "reine", "soldat", "policier", "pompier", "docteur", "infirmier", "professeur", "élève",
    "musicien", "chanteur", "acteur", "peintre", "photographe", "scientifique", "ingénieur", "cuisinier", "serveur", "plombier",
    "cœur", "étoile", "nuage", "pluie", "neige", "orage", "arc-en-ciel", "vent", "feu", "glace",
    "crayon", "gomme", "colle", "règle", "cartable", "livre", "feuille", "tableau", "craie", "trousse",
    "piano", "guitare", "violon", "batterie", "flûte", "tambour", "trompette", "microphone", "radio", "enceinte",
    "pantalon", "robe", "jupe", "pull", "tee-shirt", "manteau", "chapeau", "casquette", "chaussette", "chaussure",
    "dent", "main", "pied", "jambe", "bras", "tête", "nez", "bouche", "oreille", "œil",
    "plage", "forêt", "désert", "île", "volcan", "caverne", "ville", "village", "route", "pont",
    "horloge", "montre", "calendrier", "téléphone", "clavier", "souris", "écran", "prise", "câble", "batterie",
    "ballerine", "robot", "extraterrestre", "vaisseau", "fusée", "satellite", "planète", "galaxie", "univers", "télescope",
    "cadenas", "clé", "trésor", "carte", "boussole", "valise", "sac", "lunettes", "miroir", "brosse",
    "savon", "shampoing", "serviette", "douche", "baignoire", "toilettes", "lavabo", "brosse à dents", "dentifrice", "peigne"
]


def get_local_word():
    return choice(dictionary)

def get_word(guessed_words):
    '''Assume word unicity for the same game'''
    while True:
        word = get_word2()
        if word not in guessed_words:
            guessed_words.append(word)
            break

    return word

def get_word2():
    try:
        url = "https://random-words-api.vercel.app/word/french"
        resp = requests.get(url)
        if resp.ok:
            #print(resp.text)
            doc = resp.json()
            #print(doc)
            word = doc[0]['word']
            return word

        return get_local_word()
    except Exception as e:
        return get_local_word()

if __name__ == '__main__':
    print(get_word())
  
