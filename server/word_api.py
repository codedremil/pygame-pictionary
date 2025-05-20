'''
Gestion des mots issus d'un dictionnaire distant
'''
from random import choice
import requests


dictionary = [
    "chaise",
    "fauteuil",
    "téléphone",
    "bouteille",
    "lunettes",
    "parapluie",
    "sac à dos",
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
  
