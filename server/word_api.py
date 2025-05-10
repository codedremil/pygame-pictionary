'''
Gestion des mots issus d'un dictionnaire distant
'''
from random import choice
import requests



mot_deja_devines = {}

dictionary = [
    "chaise",
    "fauteuil",
    "téléphone",
    "bouteille",
    "lunettes",
    "parapluie",
    "sac à dos",
]

def get_local_word(player):
    word = choice(dictionary)
    while word in mot_deja_devines[player]:
        word = choice(dictionary)
    ajouter_dans_le_dico(word,player)    
    
    return word

def get_word(player):

    if player not in mot_deja_devines:
        mot_deja_devines[player] = []
        # creation d'un dictionnaire si le dictionnaire n'est pas cree
    
    try:
        url = "https://random-words-api.vercel.app/word/french"
        
        resp = requests.get(url)
        if resp.ok:
            
            doc = resp.json()
            
            word = doc[0]['word']


            if word not in mot_deja_devines[player]:
                # ajout dans le dictionnaire du mot qui va etre devine SSi le mot n'a pas deja ete fait devine 
                ajouter_dans_le_dico(word, player)   
                                             
                return word
            else:
                return get_local_word(player)

        return get_local_word(player)
    except Exception as e:
        return get_local_word(player)  

# ajouter mot dans le dictionnaire
def ajouter_dans_le_dico(word, player):
    mot_deja_devines[player].append(word)





if __name__ == '__main__':
    print(get_word())
  
