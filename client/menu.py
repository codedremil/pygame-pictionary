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
        self.client.set_callback(Protocol.EVENT_ERROR, self.recv_error)
        self.client.set_callback(Protocol.EVENT_START_GAME, self.recv_event_start_game)
        self.client.set_callback(Protocol.EVENT_JOIN_GAME, self.recv_event_join_game)
        self.client.set_callback(Protocol.EVENT_LEAVE_GAME, self.recv_event_leave_game)
        self.game_created = False
        self.game_joined = False
        self.game_started = False
        self.is_master = False  # True si on doit faire deviner
        self.word_to_guess = None
        self.active_games = None  # liste des jeux auxquels on peut participer

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
            if self.game_started and not self.is_master:
                print("6-Deviner le mot")
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
                6: self.guess_word,
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

    def recv_event_start_game(self):
        logging.info("Le jeu a démarré !")
        self.game_started = True

    def recv_event_join_game(self, player_name):
        logging.info(f"{player_name} a rejoint le jeu")

    def recv_event_leave_game(self, player_name):
        logging.info(f"{player_name} a quitté le jeu")

    def recv_error(self, msg):
        logging.error(msg)

    def guess_word(self):
        word = input("Quel mot ? ")
        found = self.client.guess_word(word)
        if found:
            logging.info("Bravo !")
        else:
            logging.info("et non...")

