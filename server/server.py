'''
Implémente le serveur de jeu
'''
import sys
import os
import time
import configparser

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, '..', 'common'))

import threading
import socket
import logging
import traceback
from unidecode import unidecode
from player import Player
from game import Game
from protocol import Protocol
from word_api import get_word


class Server:
    def __init__(self, host, port, countdown_time, guess_time):
        self.host = host
        self.port = port
        self.sock = None
        self.countdown_time = countdown_time
        self.guess_time = guess_time
        self.players = {}  # la clé est le nom
        self.lock_players = threading.Lock()
        self.games = {}  # la clé est le nom
        self.lock_games = threading.Lock()

    def start(self):
        '''
        Crée le serveur et accepte les connexions entrantes
        '''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))

        logging.info(f'Server is listening on the port {self.port}...')
        self.sock.listen()

        while True:
            self.accept_connections()

    def accept_connections(self):
        '''
        Bloque en attendant une nouvelle connexion de la part d'un client (=joueur).
        Quand le client se connecte on démarre un nouveau Thread pour le gérer.
        '''
        conn, addr = self.sock.accept()
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's Algorithm
        logging.debug("New connection !")

        # Quand le Thread démarre, il appelle la méthode new_connection() !
        thread = threading.Thread(target=self.new_connection, args=(conn,))
        thread.start()

    def new_connection(self, conn):
        '''Connexion de contrôle ou pour les événements ?'''
        player = None

        try:
            proto = Protocol(conn)

            # il faut obtenir le nom du joueur et tester l'unicité du nom du joueur 
            while True:
                msg = proto.get_message()
                if 'cmd' not in msg:
                    raise Exception(f"cmd missing - wrong Protocol")

                if msg['cmd'] != Protocol.CLI_SEND_NEW_PLAYER:
                    raise Exception(f"Wrong message type {msg['cmd']}")

                player_name = msg['name']
                conn_type = msg['type']
                logging.info(f"Player name is: {player_name} [{conn_type=}]")

                if conn_type == Protocol.TYPE_CMD:
                    if self.is_name_available(player_name):
                        player = Player(player_name, proto)
                        self.add_player(player)
                        proto.send_message_ok({})
                        self.handle_protocol(player, proto)
                        break

                    logging.error(f"Nom de joueur {player_name} déjà pris !")
                    proto.send_message_error("Ce nom de joueur est déjà pris !")
                elif conn_type == Protocol.TYPE_EVENT:
                    # Cherche le player pour lui associer la 2ème cnx
                    if self.players[player_name].get_event_channel():
                        raise Exception(f"Event_channel déjà associé au joueur {player_name}")

                    self.players[player_name].set_event_channel(proto)
                    self.players[player_name].cmd_channel.send_message_ok({})
                    while True:
                        msg = proto.get_message()
                        logging.debug(f"rcvd event message: {msg}")
                        if not msg:
                            break

                    break
                else:
                    raise Exception(f"Wrong connection type: {conn_type}")
        except Exception as e:
            logging.error(f"Exception in new_player {e}")
            traceback.print_stack()
            raise e

        if player:
            logging.info(f"player {player.name} removed")
            self.remove_player(player)

        conn.close()

    def is_name_available(self, name):
        with self.lock_players:
            return name not in self.players

    def add_player(self, player):
        logging.debug(f"add player {player.name}")
        with self.lock_players:
            self.players[player.name] = player

    def remove_player(self, player):
        player_name = player.name
        logging.debug(f"remove player {player_name}")
        with self.lock_players:
            del self.players[player_name]

        # Supprime le joueur de tous les jeux
        with self.lock_games:
            for game_name, game in self.games.items():
                if player_name in game.players:
                    logging.debug(f"player is removed from game {game.name}")
                    game.players.remove(player_name)  # pas de Lock
                    for other_player_name in game.players:
                        self.players[other_player_name].event_channel.send_event_leave_game(player_name)
                    break  # un seul jeu par joueur

        # Si le joueur était maitre d'un jeu, il faut avertir les autres joueurs
        # et choisir un nouveau maitre
        if player.game and player.game.master_player == player_name:
            # TODO: avertir les autres et choisir un nouveau master
            # Il faut arrêter les comptes à rebours éventuels !
            logging.info(f"player was a game master !")

        self._remove_games()

    def _remove_games(self):
        # Si un jeu ne dispose plus de joueurs, il faut détruire le jeu !
        games_to_be_deleted = []
        with self.lock_games:
            for game_name, game in self.games.items():
                if len(game.players) == 0:
                    games_to_be_deleted.append(game_name)

            for game_name in games_to_be_deleted:
                logging.info(f"game {game_name} has no player and is deleted")
                del self.games[game_name]

                # Avertit tous les joueurs restants que le jeu n'est plus disponible
                # pour que leur IHM se mette à jour !
                with self.lock_players:
                    for _, player in self.players.items():
                        player.event_channel.send_event_end_game(game_name)

    def handle_protocol(self, player, proto):
        '''Gère les échanges avec un joueur'''
        while True:
            msg = proto.get_message()
            logging.debug(f"recvd message: {msg}")
            if not msg:
                break

            if "cmd" not in msg:
                logging.info("Command missing")
                #continue
                break

            cmd = msg["cmd"]
            if cmd not in proto_commands:
                logging.info(f"Unknown command: {cmd}")
                #continue
                break

            proto_commands[cmd](self, player, proto, msg)

    # Les Callbacks ont 3 parametres: player, proto et msg !

    def recv_list_players(self, player, proto, msg):
        logging.debug("recv_list_players called")
        with self.lock_players:
            names = list(self.players)
            proto.send_resp_list_players(len(self.players), sorted(names))

    def recv_new_game(self, player, proto, msg):
        logging.debug("recv_new_game called")
        with self.lock_games:
            # Vérifie que le joueur n'a pas déjà créé une partie
            # (normalement fait par le Client mais il faut le faire aussi ici)
            if player.name in self.games:
                proto.send_message_error("Une partie avec ce nom existe déjà !")
                return

            self.games[player.name] = Game(player)

        proto.send_resp_new_game()

        # Indique l'événement à tous les joueurs
        with self.lock_players:
            for player_name in self.players:
                try:
                    self.players[player_name].event_channel.send_event_new_game(player.name)
                except Exception as e:
                    logging.error(f"get_message: {e}")
                    self.abort_player(player_name)

    def recv_list_game_players(self, player, proto, msg):
        logging.debug("recv_list_game_players called")
        if "game_name" not in msg:
            logging.error("protocol error")
            proto.send_message_error("Il manque le nom du jeu !")
            return

        with self.lock_games:
            game_name = msg['game_name']
            if game_name not in self.games:
                logging.error(f"game {game_name} unknown")
                proto.send_message_error("Le nom du jeu est inconnu !")
                return

            proto.send_resp_list_game_players(
                len(self.games[game_name].players),
                self.games[game_name].players
            )

    def recv_list_games(self, player, proto, msg):
        logging.debug("recv_list_games called")
        with self.lock_games:
            names = list(self.games)
            proto.send_resp_list_games(len(self.games), sorted(names))

    def recv_join_game(self, player, proto, msg):
        logging.debug("recv_join_game called")
        if "game_name" not in msg:
            logging.error("protocol error")
            proto.send_message_error("Il manque le nom du jeu !")
            return

        logging.info(f"player {player.name} joins game {msg['game_name']}")

        # Ajoute le joueur au jeu
        with self.lock_games:
            game_name = msg['game_name']
            if game_name not in self.games:
                logging.error(f"game {game_name} unknown")
                proto.send_message_error("Le nom du jeu est inconnu !")
                return

            game = self.games[game_name]
            game.add_player(player)
            # Répond au joueur
            proto.send_resp_join_game()

            # Indique l'événement à tous les joueurs
            for player_name in game.players:
                try:
                    self.players[player_name].event_channel.send_event_join_game(player.name)
                except Exception as e:
                    logging.error(f"get_message: {e}")
                    self.abort_player(player_name)

            # TODO: si le jeu a démarré et le dessin commencé, il faut envoyer le dessin courant !
            if game.started:
                # le joueur qui vient de se connecter doit savoir que le jeu a démarré
                player.event_channel.send_event_start_game(game.master_player)


    def recv_leave_game(self, player, proto, msg):
        logging.debug("recv_leave_game called")
        if "game_name" not in msg:
            logging.error("protocol error")
            proto.send_message_error("Il manque le nom du jeu !")
            return

        logging.info(f"player {player.name} left game {msg['game_name']}")

        # Supprime le joueur du jeu
        with self.lock_games:
            game_name = msg['game_name']
            if game_name not in self.games:
                logging.error(f"game {game_name} unknown")
                proto.send_message_error("Le nom du jeu est inconnu !")
                return

            game = self.games[game_name]
            game.remove_player(player)
            proto.send_resp_leave_game()

            # Indique l'événement à tous les joueurs sauf si le jeu a été détruit
            if game and len(game.players):
                for player_name in game.players:
                    try:
                        self.players[player_name].event_channel.send_event_leave_game(player.name)
                    except Exception as e:
                        logging.error(f"get_message: {e}")
                        self.abort_player(player_name)

    def recv_start_game(self, player, proto, msg):
        logging.debug("recv_start_game called")
        if "game_name" not in msg:
            logging.error("protocol error")
            proto.send_message_error("Il manque le nom du jeu !")
            return

        player.game.word_to_guess = get_word(player.game.guessed_words)
        proto.send_resp_start_game(player.game.word_to_guess)
        player.game.word_to_guess = unidecode(player.game.word_to_guess)

        # démarre un thread pour le compte à rebours
        player.game.countdown_thread = threading.Thread(target=self.countdown, args=(player.game, self.countdown_time,))
        player.game.countdown_thread.start()

    def recv_guess_word(self, player, proto, msg):
        logging.debug("recv_guess_word")
        if "word" not in msg:
            logging.error("protocol error")
            proto.send_message_error("Il manque le mot à deviner !")
            return

        logging.debug(f"{player.game.word_to_guess=}, {msg['word']=}")
        found = player.game.word_to_guess == unidecode(msg['word'])
        proto.send_resp_guess_word(found)

        # Indique l'événement à tous les joueurs
        with player.game.lock_players:
            if found:
                # Calcule le nom du prochain dessinateur
                self._get_new_master(player.game)
                player.game.started = False
                for player_name in player.game.players:
                    try:
                        self.players[player_name].event_channel.send_word_found(player.name,
                                                                                player.game.word_to_guess,
                                                                                player.game.master_player)
                    except Exception as e:
                        logging.error(f"get_message: {e}")
                        self.abort_player(player_name)
            else:
                for player_name in player.game.players:
                    try:
                        self.players[player_name].event_channel.send_word_not_found(player.name, msg['word'])
                    except Exception as e:
                        logging.error(f"get_message: {e}")
                        self.abort_player(player_name)

    def recv_draw(self, player, proto, msg):
        logging.debug(f"recv_draw {msg=}")

        # Indique l'événement à tous les autres joueurs
        with player.game.lock_players:
            for player_name in player.game.players:
                if player.name != player_name:
                    try:
                        self.players[player_name].event_channel.send_event_draw(msg)
                    except Exception as e:
                        logging.error(f"get_message: {e}")
                        self.abort_player(player_name)

    def countdown(self, game, seconds):
        while seconds:
            with game.lock_players:
                for player_name in game.players:
                    try:
                        self.players[player_name].event_channel.send_event_countdown_starting(seconds, game.master_player)
                    except Exception as e:
                        logging.error(f"get_message: {e}")
                        self.abort_player(player_name)

            time.sleep(1)
            logging.debug(f"tick {seconds=}")
            seconds -= 1

        with game.lock_players:
            for player_name in game.players:
                try:
                    self.players[player_name].event_channel.send_event_start_game(game.master_player)
                except Exception as e:
                    logging.error(f"get_message: {e}")
                    self.abort_player(player_name)

        game.started = True

        # démarre un compte à rebours de la partie (on sort si qq'un a trouvé !)
        seconds = self.guess_time
        while seconds >= 0 and game.started:
            with game.lock_players:
                for player_name in game.players:
                    try:
                        self.players[player_name].event_channel.send_event_countdown_playing(seconds)
                    except Exception as e:
                        logging.error(f"get_message: {e}")
                        self.abort_player(player_name)

            time.sleep(1)
            seconds -= 1

        # Si game.started est faux, c'est que qq'un a trouvé sinon on avertit la fin du jeu!
        if game.started:
            self._get_new_master(game)
            game.started = False
            with game.lock_players:
                for player_name in game.players:
                    try:
                        self.players[player_name].event_channel.send_event_round_end(game.word_to_guess, game.master_player)
                    except Exception as e:
                        logging.error(f"get_message: {e}")
                        self.abort_player(player_name)

    def abort_player(self, player_name):
        '''Indique que le joueur a disparu et le supprimer du jeu'''
        logging.info(f"Player {player_name} encountered a network problem")
        if player_name in self.players:
            self.remove_player(self.players[player_name])

    def _get_new_master(self, game):
        # Calcule le nom du prochain dessinateur
        try:
            idx = game.players.index(game.master_player)
        except:
            idx = -1

        game.master_player = game.players[(idx + 1) % len(game.players)]

# Liste des commandes
proto_commands = {
    Protocol.CLI_SEND_LIST_PLAYERS: Server.recv_list_players,
    Protocol.CLI_SEND_LIST_GAMES: Server.recv_list_games,
    Protocol.CLI_SEND_LIST_GAME_PLAYERS: Server.recv_list_game_players,
    Protocol.CLI_SEND_NEW_GAME: Server.recv_new_game,
    Protocol.CLI_SEND_JOIN_GAME: Server.recv_join_game,
    Protocol.CLI_SEND_LEAVE_GAME: Server.recv_leave_game,
    Protocol.CLI_SEND_START_GAME: Server.recv_start_game,
    Protocol.CLI_SEND_GUESS_WORD: Server.recv_guess_word,
    Protocol.CLI_SEND_DRAW: Server.recv_draw,
}

if __name__ == '__main__':
    levels = logging.getLevelNamesMapping()

    default_values = {
        'port': 5678,
        'log_level': 'INFO',
        'countdown': 10,
        'guess_time': 60,
    }
    host = "0.0.0.0"
    port = default_values['port']
    log_level = default_values['log_level']
    countdown = default_values['countdown']
    guess_time = default_values['guess_time']

    config = configparser.ConfigParser()
    config_path = os.path.join(base_dir, "config.ini")
    config.read(config_path)
    try:
        port = int(config['global']['port'])
    except Exception as e:
        logging.error(f"{e} not in config.ini")

    try:
        countdown = int(config['global']['countdown'])
    except Exception as e:
        logging.error(f"{e} not in config.ini")

    try:
        guess_time = int(config['global']['guess_time'])
    except Exception as e:
        logging.error(f"{e} not in config.ini")

    try:
        log_level = config['global']['log_level']
    except Exception as e:
        logging.error(f"{e} not in config.ini")


    log_level = levels[log_level]
    if 'LOG_LEVEL' in os.environ:
        if os.environ['LOG_LEVEL'] in levels:
            log_level = levels[os.environ['LOG_LEVEL']]

    logging.basicConfig(level=log_level)

    server = Server(host, port, countdown, guess_time)
    server.start()

# EOF
