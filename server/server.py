'''
Implémente le serveur de jeu
'''
import sys
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, '..', 'common'))

import threading
import socket
import time
import logging
import traceback
from player import Player
from game import Game
from protocol import Protocol
from settings import HOST, PORT


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.players = {}  # la clé est le nom
        self.lock_players = threading.Lock()
        self.games = {}  # la clé est le nom
        self.lock_games = threading.Lock()

    def start(self):
        '''
        Crée le serveur et accepte les connexions entrantes
        '''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

        logging.info(f'Server is listing on the port {self.port}...')
        self.sock.listen()

        while True:
            self.accept_connections()

    def accept_connections(self):
        '''
        Bloque en attendant une nouvelle connexion de la part d'un client (=joueur).
        Quand le client se connecte on démarre un nouveau Thread pour le gérer.
        '''
        conn, addr = self.sock.accept()
        logging.debug("New connection !")

        # Quand le Thread démarre, il appelle la méthode new_connection() !
        thread = threading.Thread(target=self.new_connection, args=(conn,))
        thread.start()

    def new_connection(self, conn):
        '''Connexion de contrôle ou pour les événements ?'''
        player = None

        try:
            proto = Protocol(conn)

            # il faut obtenir le nom du joueur
            # TODO: tester l'unicité du nom du joueur ?
            msg = proto.get_message()
            if msg['cmd'] != Protocol.CLI_SEND_NEW_PLAYER:
                raise f"Wrong message type {msg['cmd']}"

            player_name = msg['name']
            conn_type = msg['type']
            logging.info(f"Player name is: {player_name}")

            if conn_type == Protocol.TYPE_CMD:
                player = Player(player_name, proto)
                self.add_player(player)
                proto.send_message_ok({})
                self.handle_protocol(player, proto)
            elif conn_type == Protocol.TYPE_EVENT:
                # Cherche le player pour lui associer la 2ème cnx
                self.players[player_name].set_event_channel(proto)
                self.players[player_name].cmd_channel.send_message_ok({})
                while True:
                    msg = proto.get_message()
                    logging.debug(f"recvd event message: {msg}")
                    if not msg:
                        break
            else:
                raise f"Wrong connection type {conn_type}"
        except Exception as e:
            logging.error(f"Exception in new_player {e}")
            traceback.print_stack()
            raise e

        if player:
            self.remove_player(player)

        conn.close()

    def add_player(self, player):
        logging.debug(f"add player {player.name}")
        with self.lock_players:
            self.players[player.name] = player

    def remove_player(self, player):
        player_name = player.name
        logging.debug(f"remove player {player_name}")
        with self.lock_players:
            del self.players[player_name]

        '''
        # Supprime l'utilisateur de tous les jeux
        with self.lock_games:
            for game_name, game in self.games.items():
                if player_name in game.players:
                    logging.debug(f"player is removed from game {game.name}")
                    game.players.remove(player_name)  # pas de Lock
                    for other_player_name in game.players:
                        self.players[other_player_name].event_channel.send_event_leave_game(player_name)
                    break  # un seul jeu par joueur

        # Si le joueur possède un jeu, il faut détruire le jeu !
        with self.lock_games:
            if player_name in self.games:
                logging.debug("player owned a game which is deleted")
                del self.games[player_name]
        '''

    def handle_protocol(self, player, proto):
        '''Gère les échanges avec un joueur'''
        while True:
            msg = proto.get_message()
            logging.debug(f"recvd message: {msg}")
            if not msg:
                break

            if "cmd" not in msg:
                logging.info("Command missing")
                continue

            cmd = msg["cmd"]
            if cmd not in proto_commands:
                logging.info(f"Unknown command: {cmd}")
                continue

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
            # TODO: vérifie que le joueur n'a pas déjà créé une partie
            # (normalement fait pas le Client mais il faut le faire aussi ici)
            self.games[player.name] = Game(player)

        proto.send_resp_new_game()


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


# Liste des commandes
proto_commands = {
    Protocol.CLI_SEND_LIST_PLAYERS: Server.recv_list_players,
    Protocol.CLI_SEND_LIST_GAMES: Server.recv_list_games,
}

if __name__ == '__main__':
    host = HOST
    port = PORT

    logging.basicConfig(level=logging.DEBUG)

    server = Server(host, port)
    server.start()

# EOF
