'''
Implémente la partie réseau du client
Les lectures sont faites par un Thread qui appelle des callbacks
'''
import socket
import logging
import threading
from protocol import Protocol

logger = logging.getLogger()


class Client:
    def __init__(self, name, host, port):
        self.server = host
        self.port = port
        self.addr = (self.server, self.port)
        self.name = name
        self.game_name = None
        self.cmd_channel = None
        self.event_channel = None
        self.thread = None
        self.callbacks = {}  # user callbacks
        self._callbacks = {
            Protocol.EVENT_ERROR: self.recv_error,
            Protocol.EVENT_NEW_GAME: self.recv_event_new_game,
            Protocol.EVENT_START_GAME: self.recv_event_start_game,
            Protocol.EVENT_JOIN_GAME: self.recv_event_join_game,
            Protocol.EVENT_LEAVE_GAME: self.recv_event_leave_game,
            Protocol.EVENT_END_GAME: self.recv_event_end_game,
            Protocol.EVENT_DRAW: self.recv_event_draw,
            Protocol.EVENT_WORD_FOUND: self.recv_event_word_found,
            Protocol.EVENT_WORD_NOT_FOUND: self.recv_event_word_not_found,
            Protocol.EVENT_COUNTDOWN_STARTING: self.recv_event_countdown_starting,
            Protocol.EVENT_COUNTDOWN_ENDING: self.recv_event_countdown_ending,
        }
        self.connect()

    def connect(self):
        logger.debug("connect to server")
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect(self.addr)
            self.cmd_channel = Protocol(conn)
            self.cmd_channel.send_new_cmd_player(self.name)
            response = self.cmd_channel.get_message()
            logger.debug(f"Response: {response}")
            if response['rc'] != "OK":
                logging.error(response['msg'])
                raise Exception("Protocol Error")

            # Crée le channel pour les événements et lance un thread de gestion
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect(self.addr)
            self.event_channel = Protocol(conn)
            self.event_channel.send_new_event_player(self.name)
            response = self.cmd_channel.get_message()
            logging.debug(f"Response: {response}")
            if response['rc'] != "OK":
                logging.error(response['msg'])
                raise Exception("Protocol Error")

            self.thread = threading.Thread(target=self.receive_event_loop, args=())
            self.thread.setDaemon(True) # sinon, on ne peut quitter le pgm car le Thread l'empêche !
            #self.thread.daemon = True  # v3.11
            self.thread.start()
        except Exception as e:
            self.disconnect()
            raise e

    def disconnect(self):
        logger.debug("disconnect")
        if self.cmd_channel:
            self.cmd_channel.conn.close()

    def receive_event_loop(self):
        logging.debug("receive_event_loop")
        while True:
            msg = self.event_channel.get_message()
            # Le serveur a disparu !
            if not msg:
                break

            if "cmd" not in msg:
                logging.error("msg does not contain any cmd")
                continue

            cmd = msg['cmd']
            if cmd not in self._callbacks:
                logging.error(f"_callback missing for command {cmd}")
                continue

            if cmd not in self.callbacks:
                logging.error(f"callback missing for command {cmd}")
                continue

            self._callbacks[cmd](msg)

    def set_callback(self, cmd, func, *args, **kwargs):
        self.callbacks[cmd] = {"func": func, "args": args, "kwargs": kwargs}

    def get_list_players(self):
        self.cmd_channel.send_list_players()
        msg = self.cmd_channel.get_message()
        if not msg: return []

        if msg['rc'] != "OK" or 'names' not in msg:
            logging.error("Protocol error (get_list_players): {msg['msg']}")
            return []

        return msg['names']

    def get_list_games(self):
        self.cmd_channel.send_list_games()
        msg = self.cmd_channel.get_message()
        if not msg: return []

        if msg['rc'] != "OK" or 'names' not in msg:
            logging.error(f"Protocol error (get_list_games): {msg['msg']}")
            return []

        return msg['names']

    def new_game(self):
        self.cmd_channel.send_new_game()
        msg = self.cmd_channel.get_message()
        if not msg: return False 

        if msg['rc'] != "OK":
            logging.error(f"Protocol error (new_game): {msg['msg']}")
            return False 

        return True

    def start_game(self):
        self.cmd_channel.send_start_game(self.game_name)
        msg = self.cmd_channel.get_message()
        if not msg: return None

        if msg['rc'] != "OK" or 'word' not in msg:
            logging.error(f"Protocol error (start_game): {msg['msg']}")
            return None

        return msg['word']

    def join_game(self, game_name):
        self.cmd_channel.send_join_game(game_name)
        msg = self.cmd_channel.get_message()
        if not msg: return None

        if msg['rc'] != "OK":
            logging.error(f"Protocol error (join_game): {msg['msg']}")

    def leave_game(self, game_name):
        self.cmd_channel.send_leave_game(game_name)
        msg = self.cmd_channel.get_message()
        if not msg: return None

        if msg['rc'] != "OK":
            logging.error(f"Protocol error (leave_game): {msg['msg']}")

    def get_list_game_players(self, game_name=None):
        if game_name is None:
            game_name = self.game_name

        self.cmd_channel.send_list_game_players(game_name)
        msg = self.cmd_channel.get_message()
        if not msg: return []

        if msg['rc'] != "OK" or 'names' not in msg:
            logging.error("Protocol error (get_list_game_players): {msg['msg']}")
            return []

        return msg['names']

    def send_plot(self, x, y, color):
        '''color est un tuple (R, G, B)'''
        if type(color) is not tuple:
            color = tuple(color)

        self.cmd_channel.send_draw({"action": "plot", "x": x, "y": y, "color": color})

    def send_clear(self):
        self.cmd_channel.send_draw({"action": "clear"})

    def recv_error(self, msg):
        self.callbacks[Protocol.EVENT_ERROR]['func'](msg['msg'])

    def recv_event_new_game(self, msg):
        if msg['rc'] != "OK" or 'name' not in msg:
            logger.error(f"Protocol error (recv_event_new_game): {msg['msg']}")
            return

        self.callbacks[Protocol.EVENT_NEW_GAME]['func'](msg['name'])

    def recv_event_start_game(self, msg):
        self.callbacks[Protocol.EVENT_START_GAME]['func']()

    def recv_event_end_game(self, msg):
        if msg['rc'] != "OK" or 'name' not in msg:
            logger.error(f"Protocol error (recv_event_end_game): {msg['msg']}")
            return

        self.callbacks[Protocol.EVENT_END_GAME]['func'](msg['name'])

    def recv_event_join_game(self, msg):
        if msg['rc'] != "OK" or 'name' not in msg:
            logging.error(f"Protocol error (recv_event_join_game): {msg['msg']}")
            return

        self.callbacks[Protocol.EVENT_JOIN_GAME]['func'](msg['name'])

    def recv_event_leave_game(self, msg):
        if msg['rc'] != "OK" or 'name' not in msg:
            logging.error(f"Protocol error (recv_event_leave_game): {msg['msg']}")
            return

        self.callbacks[Protocol.EVENT_LEAVE_GAME]['func'](msg['name'])

    def recv_event_draw(self, msg):
        if msg['rc'] != "OK":
            logging.error(f"Protocol error (recv_event_draw): {msg['msg']}")
            return

        self.callbacks[Protocol.EVENT_DRAW]['func'](msg)

    def recv_event_word_found(self, msg):
        if msg['rc'] != "OK" or "winner" not in msg or "word" not in msg:
            logging.error(f"Protocol error (recv_event_word_found): {msg['msg']}")
            return

        self.callbacks[Protocol.EVENT_WORD_FOUND]['func'](msg['winner'], msg['word'])

    def recv_event_word_not_found(self, msg):
        if msg['rc'] != "OK" or "player" not in msg or "word" not in msg:
            logging.error(f"Protocol error (recv_event_word_not_found): {msg['msg']}")
            return

        self.callbacks[Protocol.EVENT_WORD_NOT_FOUND]['func'](msg['player'], msg['word'])

    def guess_word(self, word):
        self.cmd_channel.send_guess_word(word)
        msg = self.cmd_channel.get_message()
        if not msg: return False

        if msg['rc'] != "OK" or 'found' not in msg:
            logging.error("Protocol error (guess_word): {msg['msg']}")
            return False

        return msg['found']

    def recv_event_countdown_starting(self, msg):
        if msg['rc'] != 'OK' or 'seconds' not in msg:
            logging.error(f"Protocol error (recv_event_countdown_starting): {msg['msg']}")
            return

        self.callbacks[Protocol.EVENT_COUNTDOWN_STARTING]['func'](msg['seconds'])

    def recv_event_countdown_ending(self, msg):
        if msg['rc'] != 'OK' or 'seconds' not in msg:
            logging.error(f"Protocol error (recv_event_countdown_ending): {msg['msg']}")
            return

        self.callbacks[Protocol.EVENT_COUNTDOWN_ENDING]['func'](msg['seconds'])

