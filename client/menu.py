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
        self.game_created = False
        self.game_joined = False
        self.game_started = False


    def run(self):
        '''Affiche l'interface texte de connexion au jeu'''
        while True:
            print("Fais ton choix !")
            print("0-Quitter")
            print("1-Voir la liste des autres joueurs")
            print("2-Voir la liste des parties en attente")
            if not self.game_created and not self.game_joined:
                print("4-Créer une nouvelle partie")
                print("5-Joindre une partie")
            if self.game_created or self.game_joined:
                print("7-Quitter la partie")
                print("8-Voir la liste des joueurs de la partie")
            if self.game_created and not self.game_started:
                print("9-Démarrer la partie")

            try:
                choice = int(input("? "))
            except:
                print("Je ne comprends pas...")
                continue

            actions = {
                0: sys.exit,
                1: self.get_list_players,
                2: self.get_list_games,
                4: self.new_game,
                5: self.join_game,
                7: self.leave_game,
                8: self.get_list_game_players,
                9: self.start_game,
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

    def get_list_game_players(self):
        # Display the list of the connected players for the current game
        names = self.client.get_list_game_players()
        logging.info(f"Il y a {len(names)} joueurs connectés:")
        for player in names:
            logging.info(player)

    def new_game(self):
        self.client.new_game()
        self.game_created = True
        # Le jeu porte le nom du Client
        self.client.game_name = self.client.name

    def start_game(self):
        logging.debug("LE JEU DOIT DEMARRER !")
        word = self.client.start_game()
        self.game_started = True
        self.is_master = True
        self.word_to_guess = word
        logging.info(f"Tu dois faire deviner le mot '{word}'")

    def join_game(self):
        # Display the list of games to make the player choose one:
        self.get_list_games()
        time.sleep(1)
        print("Choisis le jeu dans la liste suivante:")
        for idx, name in enumerate(self.active_games):
            print(f"{idx}-{name}")

        try:
            choice = int(input("? "))
        except:
            print("Je ne comprends pas...")
            return

        if choice > len(self.active_games):
            print("Numéro inconnu")
            return

        self.client.join_game(self.active_games[idx - 1])
        self.client.game_name = self.active_games[idx - 1]
        self.game_joined = True

    def leave_game(self):
        self.client.leave_game(self.client.game_name)
        self.game_joined = False

