import sys
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, '..', 'common'))

import logging
from menu import Menu
from client import Client
from settings import HOST, PORT


def main():
    '''Affiche l'interface texte de connexion au jeu'''
    while True:
        player_name = input("Donnez votre nom de joueur: ")
        try:
            client = Client(player_name, HOST, PORT)
            break
        except Exception as e:
            print(e)

    menu = Menu(client)
    menu.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()

