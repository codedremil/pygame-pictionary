'''
Implémente le protocole (format JSON)
'''
import json
import logging


class Protocol:
    TYPE_CMD = "CMD"
    TYPE_EVENT = "EVENT"

    # Commandes possibles (Client => Server)
    CLI_SEND_NEW_PLAYER = "CLI_SEND_NEW_PLAYER"     # send = {name,conn_type}
    CLI_SEND_LIST_PLAYERS = "CLI_SEND_LIST_PLAYERS"   # send = {}
    CLI_SEND_LIST_GAMES = "CLI_SEND_LIST_GAMES"       # send = {}
    CLI_SEND_LIST_GAME_PLAYERS = "CLI_SEND_LIST_GAME_PLAYERS" # send = {game_name}
    CLI_SEND_NEW_GAME = "CLI_SEND_NEW_GAME"       # send = {}
    CLI_SEND_START_GAME = "CLI_SEND_START_GAME"   # send = {game_name}
    CLI_SEND_JOIN_GAME = "CLI_SEND_JOIN_GAME"     # send = {game_name}
    CLI_SEND_LEAVE_GAME = "CLI_SEND_LEAVE_GAME"   # send = {game_name}
    CLI_SEND_GUESS_WORD = "CLI_SEND_GUESS_WORD"   # send = {word}
    CLI_SEND_DRAW = "CLI_SEND_DRAW"               # send = {x, y, color}

    # Réponses possibles (Serveur => Client)
    SRV_RESP_LIST_PLAYERS = "SRV_RESP_LIST_PLAYERS"     # send = {count, players}
    SRV_RESP_LIST_GAMES = "SRV_RESP_LIST_GAMES"         # send = {count, names}
    SRV_RESP_LIST_GAME_PLAYERS = "SRV_RESP_LIST_GAME_PLAYERS"   # send = {count, players}
    SRV_RESP_NEW_GAME = "SRV_RESP_NEW_GAME"         # send = {}
    SRV_RESP_START_GAME = "SRV_RESP_START_GAME"     # send = {word}  = word_to_guess
    SRV_RESP_GUESS_WORD = "SRV_RESP_GUESS_WORD"     # send = {ok/nok}
    SRV_RESP_JOIN_GAME = "SRV_RESP_JOIN_GAME"     # send = {}
    SRV_RESP_LEAVE_GAME = "SRV_RESP_LEAVE_GAME"   # send = {}

    # Evenements possibles (Server => Client)
    EVENT_ERROR = "EVENT_ERROR"
    EVENT_NEW_GAME = "EVENT_NEW_GAME"     # send = {name}   # = game_name
    EVENT_JOIN_GAME = "EVENT_JOIN_GAME"     # send = {name, attrs}   # = player_name
    EVENT_LEAVE_GAME = "EVENT_LEAVE_GAME"   # send = {name}   # = player_name
    EVENT_START_GAME = "EVENT_START_GAME"   # send = {master_player}
    EVENT_END_GAME = "EVENT_END_GAME"       # send = {name} # game_name
    EVENT_DRAW = "EVENT_DRAW"               # send = {action=plot + (x, y, color) | action=clear}
    EVENT_WORD_FOUND = "EVENT_WORD_FOUND"   # send = {winner, word, new_master}
    EVENT_WORD_NOT_FOUND = "EVENT_NOT_WORD_FOUND"   # send = {word, player} 
    EVENT_COUNTDOWN_STARTING = "EVENT_COUNTDOWN_STARTING"     # send {seconds, master_player}
    EVENT_COUNTDOWN_ENDING = "EVENT_COUNTDOWN_ENDING"     # send {seconds}
    EVENT_COUNTDOWN_PLAYING = "EVENT_COUNTDOWN_PLAYING"     # send {seconds}
    EVENT_ROUND_END = "EVENT_ROUND_END" # send = {word, master_player}
    EVENT_UPDATE_PLAYER = "EVENT_UPDATE_PLAYER" # send = {player, new_score}


    def __init__(self, conn):
        self.conn = conn    # socket
        self._buffer = ''

    def get_message(self):
        logging.debug("-> get_message")
        json_data = {}

        try:
            # Les messages peuvent arriver en plusieurs "morceaux", 
            # il faut attendre le \n final
            while True:
                # Test si le buffer contient un reliquat de ligne
                if '\n' in self._buffer:
                    data, self._buffer = self._buffer.split('\n', 1)
                    json_data = json.loads(data)
                    logging.debug(f"got line: {json_data=}")
                    break

                chunk = self.conn.recv(1024).decode('utf-8')
                logging.debug(f"{chunk=}")
                if not chunk:
                    break

                self._buffer += chunk
        except Exception as e:
            logging.error(f"get_message: {e}")
            raise e

        logging.debug(json_data)
        return json_data


    def send_message(self, dict_msg):
        self.conn.sendall(json.dumps(dict_msg).encode('utf-8') + b'\n')

    def send_message_ok(self, dict_msg):
        response =  {"rc": "OK", **dict_msg}
        self.conn.sendall(json.dumps(response).encode('utf-8') + b'\n')

    #def send_message_error(self, msg, dict_msg):
    def send_message_error(self, msg):
        #response =  {"rc": "ERROR", "cmd": Protocol.EVENT_ERROR, "msg": msg, **dict_msg}
        response =  {"rc": "ERROR", "cmd": Protocol.EVENT_ERROR, "msg": msg}
        self.conn.sendall(json.dumps(response).encode('utf-8') + b'\n')

    # Les requêtes proviennent du client
    def send_new_cmd_player(self, player_name):
        self.send_message({"cmd": Protocol.CLI_SEND_NEW_PLAYER, "name": player_name, "type": Protocol.TYPE_CMD})

    def send_new_event_player(self, player_name):
        self.send_message({"cmd": Protocol.CLI_SEND_NEW_PLAYER, "name": player_name, "type": Protocol.TYPE_EVENT})

    def send_list_players(self):
        self.send_message({"cmd": Protocol.CLI_SEND_LIST_PLAYERS})

    def send_new_game(self):
        self.send_message({"cmd": Protocol.CLI_SEND_NEW_GAME})

    def send_list_games(self):
        self.send_message({"cmd": Protocol.CLI_SEND_LIST_GAMES})

    def send_join_game(self, game_name):
        self.send_message({"cmd": Protocol.CLI_SEND_JOIN_GAME, "game_name": game_name})

    def send_leave_game(self, game_name):
        self.send_message({"cmd": Protocol.CLI_SEND_LEAVE_GAME, "game_name": game_name})

    def send_start_game(self, game_name):
        self.send_message({"cmd": Protocol.CLI_SEND_START_GAME, "game_name": game_name})

    def send_list_game_players(self, game_name):
        self.send_message({"cmd": Protocol.CLI_SEND_LIST_GAME_PLAYERS, "game_name": game_name})

    def send_guess_word(self, word):
        self.send_message({"cmd": Protocol.CLI_SEND_GUESS_WORD, "word": word})

    def send_draw(self, dict_msg):
        logging.debug(f"send_draw {dict_msg}")
        self.send_message({"cmd": Protocol.CLI_SEND_DRAW, **dict_msg})

    # Ces réponses sont envoyées par le serveur
    def send_resp_join_game(self):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_JOIN_GAME})

    def send_resp_list_players(self, count, players):
        '''players est un dictionnaire avec le nom du joueur comme clé. Contient le score.'''
        self.send_message_ok({"cmd": Protocol.SRV_RESP_LIST_PLAYERS, "count": count, "players": dict(sorted(players.items()))})

    def send_resp_start_game(self, word):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_START_GAME, "word": word})

    def send_resp_leave_game(self):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_LEAVE_GAME})

    def send_resp_list_game_players(self, count, players):
        '''players est un dictionnaire avec le nom du joueur comme clé. Contient le score.'''
        self.send_message_ok({"cmd": Protocol.SRV_RESP_LIST_GAME_PLAYERS, "count": count, "players": dict(sorted(players.items()))})

    def send_resp_list_games(self, count, names):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_LIST_GAMES, "count": count, "names": names})

    def send_resp_new_game(self):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_NEW_GAME})

    def send_resp_guess_word(self, found):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_GUESS_WORD, "found": found})

    # Les événements sont envoyés par le serveur
    def send_event_new_game(self, player_name):
        self.send_message_ok({"cmd": Protocol.EVENT_NEW_GAME, "name": player_name})

    def send_event_join_game(self, player_name, attrs):
        self.send_message_ok({"cmd": Protocol.EVENT_JOIN_GAME, "name": player_name, "attrs": attrs})

    def send_event_leave_game(self, player_name):
        self.send_message_ok({"cmd": Protocol.EVENT_LEAVE_GAME, "name": player_name})

    def send_event_start_game(self, master_player):
        self.send_message_ok({"cmd": Protocol.EVENT_START_GAME, "master_player": master_player})

    def send_event_end_game(self, game_name):
        self.send_message_ok({"cmd": Protocol.EVENT_END_GAME, "name": game_name})

    def send_event_guess_word(self, word):
        self.send_message_ok({"cmd": Protocol.EVENT_GUESS_WORD, "word": word})

    def send_word_found(self, winner, score, word, new_master):
        self.send_message_ok({"cmd": Protocol.EVENT_WORD_FOUND, "word": word, "winner": winner, "score": score, "master": new_master})

    def send_word_not_found(self, player, word):
        self.send_message_ok({"cmd": Protocol.EVENT_WORD_NOT_FOUND, "word": word, "player": player})

    def send_event_draw(self, dict_msg):
        if 'cmd' in dict_msg:
            del dict_msg['cmd']

        self.send_message_ok({"cmd": Protocol.EVENT_DRAW, **dict_msg})

    def send_event_countdown_starting(self, seconds, master_player):
        self.send_message_ok({"cmd": Protocol.EVENT_COUNTDOWN_STARTING, "seconds": seconds, "master_player": master_player})

    def send_event_countdown_playing(self, seconds):
        self.send_message_ok({"cmd": Protocol.EVENT_COUNTDOWN_PLAYING, "seconds": seconds})

    # inutilisé ?
    def send_event_countdown_ending(self, seconds):
        self.send_message_ok({"cmd": Protocol.EVENT_COUNTDOWN_ENDING, "seconds": seconds})

    def send_event_round_end(self, word, new_master):
        self.send_message_ok({"cmd": Protocol.EVENT_ROUND_END, "word": word, "master": new_master})

    def send_event_update_player(self, player, new_attrs):
        self.send_message_ok({"cmd": Protocol.EVENT_UPDATE_PLAYER, "player": player, "attrs": new_attrs})

