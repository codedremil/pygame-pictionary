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
    SRV_RESP_LIST_PLAYERS = "SRV_RESP_LIST_PLAYERS"     # send = {count, names}
    SRV_RESP_LIST_GAMES = "SRV_RESP_LIST_GAMES"         # send = {count, names}
    SRV_RESP_LIST_GAME_PLAYERS = "SRV_RESP_LIST_GAME_PLAYERS"   # send = {count, names}
    SRV_RESP_NEW_GAME = "SRV_RESP_NEW_GAME"         # send = {}
    SRV_RESP_START_GAME = "SRV_RESP_START_GAME"     # send = {word}  = word_to_guess
    SRV_RESP_GUESS_WORD = "SRV_RESP_GUESS_WORD"     # send = {ok/nok}
    SRV_RESP_JOIN_GAME = "SRV_RESP_JOIN_GAME"     # send = {}
    SRV_RESP_LEAVE_GAME = "SRV_RESP_LEAVE_GAME"   # send = {}

    # Evenements possibles (Server => Client)
    EVENT_ERROR = "EVENT_ERROR"
    EVENT_NEW_GAME = "EVENT_NEW_GAME"     # send = {name}   # = game_name
    EVENT_JOIN_GAME = "EVENT_JOIN_GAME"     # send = {name}   # = player_name
    EVENT_LEAVE_GAME = "EVENT_LEAVE_GAME"   # send = {name}   # = player_name
    EVENT_START_GAME = "EVENT_START_GAME"   # send = {}
    EVENT_END_GAME = "EVENT_END_GAME"       # send = {name} # game_name
    EVENT_DRAW = "EVENT_DRAW"               # send = {action=plot + (x, y, color) | action=clear}
    EVENT_WORD_FOUND = "EVENT_WORD_FOUND"   # send = {winner, word}
    EVENT_WORD_NOT_FOUND = "EVENT_WORD_FOUND"   # send = {word} # JD


    def __init__(self, conn):
        self.conn = conn    # socket
        self._buffer = ''

    def get_message(self):
        json_data = {}

        try:
            # Les messages peuvent arriver en plusieurs "morceaux", 
            # il faut attendre le \n final
            while True:
                chunk = self.conn.recv(1024).decode('utf-8')
                if not chunk:
                    break

                self._buffer += chunk
                if '\n' in self._buffer:
                    data, self._buffer = self._buffer.split('\n', 1)
                    json_data = json.loads(data)
                    break
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

    def send_resp_list_players(self, count, names):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_LIST_PLAYERS, "count": count, "names": names})

    def send_resp_start_game(self, word):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_START_GAME, "word": word})

    def send_resp_leave_game(self):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_LEAVE_GAME})

    def send_resp_list_game_players(self, count, names):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_LIST_GAME_PLAYERS, "count": count, "names": names})

    def send_resp_list_games(self, count, names):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_LIST_GAMES, "count": count, "names": names})

    def send_resp_new_game(self):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_NEW_GAME})

    def send_resp_guess_word(self, found):
        self.send_message_ok({"cmd": Protocol.SRV_RESP_GUESS_WORD, "found": found})

    # Les événements sont envoyés par le serveur
    def send_event_new_game(self, player_name):
        self.send_message_ok({"cmd": Protocol.EVENT_NEW_GAME, "name": player_name})

    def send_event_join_game(self, player_name):
        self.send_message_ok({"cmd": Protocol.EVENT_JOIN_GAME, "name": player_name})

    def send_event_leave_game(self, player_name):
        self.send_message_ok({"cmd": Protocol.EVENT_LEAVE_GAME, "name": player_name})

    def send_event_start_game(self):
        self.send_message_ok({"cmd": Protocol.EVENT_START_GAME})

    def send_event_end_game(self, game_name):
        self.send_message_ok({"cmd": Protocol.EVENT_END_GAME, "name": game_name})

    def send_event_guess_word(self, word):
        self.send_message_ok({"cmd": Protocol.EVENT_GUESS_WORD, "word": word})

    def send_word_found(self, winner, word):
        self.send_message_ok({"cmd": Protocol.EVENT_WORD_FOUND, "word": word, "winner": winner})

    def send_event_draw(self, dict_msg):
        if 'cmd' in dict_msg:
            del dict_msg['cmd']

        self.send_message_ok({"cmd": Protocol.EVENT_DRAW, **dict_msg})

