'''
Menu pour tester le protocole en mode texte
'''
import sys
import time
import logging
from client import Client
from protocol import Protocol


class Menu:
    def __init__(self, client):
        self.client = client

    def run(self):
        '''Affiche l'interface texte de connexion au jeu'''
        while True:
            print("Fais ton choix !")
            print("0-Quitter")
            print("1-Voir la liste des autres joueurs")
            print("2-Voir la liste des parties en attente")

            try:
                choice = int(input("? "))
            except:
                print("Je ne comprends pas...")
                continue

            actions = {
                0: sys.exit,
                1: self.get_list_players,
                2: self.get_list_games,
            }

            if choice not in actions:
                print("Numéro inconnu")
                continue

            actions[choice]()

    def get_list_players(self):
        players = self.client.get_list_players()
        if len(players) == 1:
            logging.info("Patience, tu es tout seul !")
            return

        logging.info(f"Il y a {len(players)} joueurs:")
        for name in players:
            logging.info(name)

    def get_list_games(self):
        games = self.client.get_list_games()
        logging.info(f"Il y a {len(games)} jeu(x) en attente ou en cours:")
        self.active_games = games
        for name in games:
            logging.info(name)

