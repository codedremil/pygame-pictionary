'''
Implémente l'interface graphique du jeu
'''
import sys
import os
import logging
import log
import random
import threading
import pygame
import pygame_gui
import configparser

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, '..', 'common'))

from client import Client
from protocol import Protocol
from editable_canvas import EditableCanvas

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG = BLACK
FPS = 30
WIDTH = 800
HEIGHT = 600

# Dimensions des widgets
POPUP_WIDTH = 500
POPUP_HEIGHT = 180
PSEUDO_LABEL_WIDTH = 140
SPACING = 3
LEFT_MENU_WIDTH = 100
LABEL_HEIGHT = 30
GAME_LIST_HEIGHT = 100
PLAYER_LIST_HEIGHT = 140
STATUS_BAR_HEIGHT = 20
MSGBOX_WIDTH = WIDTH
MSGBOX_HEIGHT = 100
RIGHT_TOOL_WIDTH = 100
CANVAS_WIDTH = WIDTH - LEFT_MENU_WIDTH - 2 * SPACING - RIGHT_TOOL_WIDTH
CANVAS_HEIGHT = HEIGHT - STATUS_BAR_HEIGHT - MSGBOX_HEIGHT - 2 * SPACING
TIME_WIDTH = RIGHT_TOOL_WIDTH
TIME_HEIGHT = 30
PROPOSED_WORDS_WIDTH = RIGHT_TOOL_WIDTH
PROPOSED_WORDS_HEIGHT = CANVAS_HEIGHT - TIME_HEIGHT
BUTTON_HEIGHT = 20
TOOLBAR_HEIGHT = 300
COLOR_WIDTH = 400
COLOR_HEIGHT = 400

PSEUDO_PROMPT = ' Indique ton pseudo: '
WORD_PROMPT = 'Mot> '


logger = None
display_lock = threading.Lock()


class PictGame:
    def __init__(self, width, height):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()
        #pygame.mixer.quit()
        pygame.display.set_caption('Pictionary en réseau')

        self.width = width 
        self.height = height
        self.window_surface = pygame.display.set_mode((self.width, self.height))
        self.player_name = ""
        # self.waiting = False
        self.network = None
        self.user_registered = False
        self.game_created = False
        self.selected_game = None # nom du jeu sélectionné dans la liste déroulante
        self.game = None
        self.game_started = False
        self.status_bar = ""
        self.color = pygame.Color(255, 255, 255, 255)
        self.name_font = pygame.font.SysFont("comicsans", 80)
        self.title_font = pygame.font.SysFont("comicsans", 120)
        self.enter_font = pygame.font.SysFont("comicsans", 60)
        self._get_config()
        self._build_interface()

    def _get_config(self):
        default_values = {
            'host': 'localhost',
            'port': 5678,
            'victory': 'victory.wav',
            'failure': 'failure.mp3',
            'ding': 'bell.wav',
        }
        self.server_host = default_values['host']
        self.server_port = default_values['port']
        self.victory_sound = default_values['victory']
        self.failure_sound = default_values['failure']
        self.ding_sound = default_values['ding']

        config = configparser.ConfigParser()
        config_path = os.path.join(base_dir, "config.ini")
        config.read(config_path)
        try:
            self.victory_sound = pygame.mixer.Sound(os.path.join(base_dir, "snd", config['sounds']['victory']))
        except Exception as e:
            logging.error(f"{e} est absent du fichier de configuration")

        try:
            self.failure_sound = pygame.mixer.Sound(os.path.join(base_dir, "snd", config['sounds']['failure']))
        except Exception as e:
            logging.error(f"{e} est absent du fichier de configuration")

        try:
            self.ding_sound = pygame.mixer.Sound(os.path.join(base_dir, "snd", config['sounds']['ding']))
        except Exception as e:
            logging.error(f"{e} est absent du fichier de configuration")

        try:
            self.server_host = config['server']['host']
        except Exception as e:
            logging.error(f"{e} est absent du fichier de configuration")

        try:
            self.server_port = int(config['server']['port'])
        except Exception as e:
            logging.error(f"{e} est absent du fichier de configuration")

    def _build_interface(self):
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(pygame.Color(BG))

        # Création du Manager
        self.manager = pygame_gui.UIManager((self.width, self.height), theme_path="gui.json")
        self.manager.set_locale('fr')

        # Pour la saisie du pseudo
        w, h = POPUP_WIDTH, POPUP_HEIGHT # centré (pas beau !)
        self.widget_name_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(((self.width - w) // 2 + PSEUDO_LABEL_WIDTH, (self.height - h) // 2), (w - PSEUDO_LABEL_WIDTH, h)),
            manager=self.manager,
            #initial_text=PSEUDO_PROMPT
        )
        self.widget_name_entry.change_layer(10)
        self.widget_name_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(((self.width - w) // 2, (self.height - h) // 2 + 2), (PSEUDO_LABEL_WIDTH + 3, h - 4)),
            manager=self.manager,
            text=PSEUDO_PROMPT,
        )
        self.widget_name_label.change_layer(10)

        # Pour l'affichage de l'état de la connexion avec le serveur
        h = STATUS_BAR_HEIGHT # collé en bas
        self.widget_server_status = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, self.height - h), (self.width, h)),
            manager=self.manager,
            text='Serveur: déconnecté',
        )

        # Pour l'affichage des jeux en cours
        w, h = LEFT_MENU_WIDTH, LABEL_HEIGHT # collé en haut à gauche
        label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager=self.manager,
            text='Jeux en cours :',
        )

        w, h = LEFT_MENU_WIDTH, GAME_LIST_HEIGHT # collé en haut à gauche
        self.widget_game_list = pygame_gui.elements.UISelectionList(
            #relative_rect=pygame.Rect((0, LABEL_HEIGHT), (w, h)),
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager=self.manager,
            anchors={'top': 'top', 'top_target': label},
            item_list=[],
        )

        # Pour l'affichage de la liste des joueurs
        w, h = LEFT_MENU_WIDTH, LABEL_HEIGHT # collé en haut à gauche
        label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager=self.manager,
            anchors={'top': 'top', 'top_target': self.widget_game_list},
            text='Joueurs :',
        )

        w, h = LEFT_MENU_WIDTH, PLAYER_LIST_HEIGHT # collé en haut à gauche
        self.widget_player_list = pygame_gui.elements.UISelectionList(
            #relative_rect=pygame.Rect((0, LABEL_HEIGHT), (w, h)),
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager=self.manager,
            anchors={'top': 'top', 'top_target': label},
            item_list=[],
        )

        # Pour l'affichage du temps restant
        w, h = TIME_WIDTH, TIME_HEIGHT # collé en haut à droite
        self.widget_remaining_time = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.width - TIME_WIDTH, SPACING), (w, h)),
            manager=self.manager,
            text='Temps : 00',
        )

        # Pour l'affichage des mots proposés
        w, h = PROPOSED_WORDS_WIDTH, PROPOSED_WORDS_HEIGHT # collé en haut à droite
        self.widget_proposed_words = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect((self.width - PROPOSED_WORDS_WIDTH, SPACING + TIME_HEIGHT), (w, h)),
            manager=self.manager,
            item_list=[],
        )

        # Pour créer et démarrer un jeu
        w, h = LEFT_MENU_WIDTH, BUTTON_HEIGHT
        self.widget_create_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager=self.manager,
            anchors={'top': 'top', 'top_target': self.widget_player_list},
            text='Créer partie',
        )
        self.widget_create_button.hide()

        self.widget_start_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager=self.manager,
            anchors={'top': 'top', 'top_target': self.widget_player_list},
            text='Démarrer',
        )
        self.widget_start_button.hide()

        # Pour joindre ou quitter un jeu
        w, h = LEFT_MENU_WIDTH, BUTTON_HEIGHT
        self.widget_join_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager=self.manager,
            anchors={'top': 'top', 'top_target': self.widget_create_button},
            text='Rejoindre',
        )
        self.widget_join_button.hide()
        self.widget_leave_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager=self.manager,
            anchors={'top': 'top', 'top_target': self.widget_create_button},
            text='Quitter',
        )
        self.widget_leave_button.hide()

        # Pour proposer un mot
        w, h = CANVAS_WIDTH, LABEL_HEIGHT # collé en bas du Canvas
        self.widget_word_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((LEFT_MENU_WIDTH + SPACING + 50, CANVAS_HEIGHT + SPACING - h), (w - 50, h)),
            manager=self.manager,
            #initial_text=WORD_PROMPT
        )
        self.widget_word_entry.change_layer(10)
        self.widget_word_entry.hide()
        self.widget_word_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((LEFT_MENU_WIDTH + SPACING, CANVAS_HEIGHT + SPACING - h + 2), (50 + 3, h - 4)),
            manager=self.manager,
            text=WORD_PROMPT
        )
        self.widget_word_label.change_layer(10)
        self.widget_word_label.hide()

        # Pour l'affichage des événements
        self.widget_msg = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect((0, CANVAS_HEIGHT + SPACING), (MSGBOX_WIDTH, MSGBOX_HEIGHT)),
            manager=self.manager
        )

        # Zone de dessin (Canvas)
        new_canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT), flags=pygame.SRCALPHA, depth=32)
        new_canvas.fill(WHITE)
        canvas_window_rect = pygame.Rect((LEFT_MENU_WIDTH + SPACING, SPACING), (CANVAS_WIDTH, CANVAS_HEIGHT))
        self.canvas_window = EditableCanvas(
            pict_game=self,
            relative_rect=canvas_window_rect,
            manager=self.manager,
            image_surface=new_canvas,
            lock=display_lock
        )

        # Bouton pour effacer le Canvas
        w, h = LEFT_MENU_WIDTH, BUTTON_HEIGHT
        self.widget_clear_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager= self.manager,
            anchors={'top': 'top', 'top_target': self.widget_leave_button},
            text='Efface',
        )
        self.widget_clear_button.hide()

        # Bouton pour changer de couleur de crayon
        w, h = LEFT_MENU_WIDTH, BUTTON_HEIGHT
        self.widget_color_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager= self.manager,
            anchors={'top': 'top', 'top_target': self.widget_clear_button},
            text='Couleur',
        )
        self.widget_color_button.hide()

    def _set_callbacks(self):
        self.network.set_callback(Protocol.EVENT_NEW_GAME, self.event_new_game)
        self.network.set_callback(Protocol.EVENT_JOIN_GAME, self.event_join_game)
        self.network.set_callback(Protocol.EVENT_LEAVE_GAME, self.event_leave_game)
        self.network.set_callback(Protocol.EVENT_START_GAME, self.event_start_game)
        self.network.set_callback(Protocol.EVENT_END_GAME, self.event_end_game) # JD
        self.network.set_callback(Protocol.EVENT_DRAW, self.event_draw)
        self.network.set_callback(Protocol.EVENT_WORD_FOUND, self.event_word_found)
        self.network.set_callback(Protocol.EVENT_WORD_NOT_FOUND, self.event_word_not_found)
        self.network.set_callback(Protocol.EVENT_COUNTDOWN_STARTING, self.event_countdown_starting)
        self.network.set_callback(Protocol.EVENT_COUNTDOWN_ENDING, self.event_countdown_ending)
        self.network.set_callback(Protocol.EVENT_COUNTDOWN_PLAYING, self.event_countdown_playing)
        self.network.set_callback(Protocol.EVENT_ROUND_END, self.event_round_end)

    def _get_status_bar_text(self):
        connected = "connecté" if self.network else "déconnecté"
        game_in_progress = self.game if self.game else "aucun"
        return f"Serveur: {connected}   Pseudo: {self.player_name}   Jeu: {game_in_progress}"

    def _set_status_bar_text(self):
        self.widget_server_status.set_text(self._get_status_bar_text())

    def _message(self, msg):
        '''Le message peut contenir du HTML'''
        w, h = POPUP_WIDTH, POPUP_HEIGHT # centré (pas beau !)
        pygame_gui.windows.UIMessageWindow(
                    rect=pygame.Rect(((self.width - w) // 2, (self.height - h) // 2), (w, h)),
                    manager=self.manager,
                    window_title="Message",
                    html_message=msg
                )

    def event_new_game(self, game_name):
        # Ajoute le jeu dans la liste
        if game_name != self.player_name:
            logging.info(f"{game_name} a créé un jeu !")

        self.widget_game_list.add_items([game_name])

    def event_join_game(self, player_name):
        # Ajoute le joueur dans la liste
        if player_name != self.player_name:
            logger.info(f"{player_name} a rejoint le jeu !")

        self.widget_player_list.add_items([player_name])

    def event_leave_game(self, player_name):
        # Supprime le joueur de la liste
        if player_name != self.player_name:
            logger.info(f"{player_name} a quitté le jeu !")

        self.widget_player_list.remove_items([player_name])

    def event_start_game(self, master_player):
        # Le jeu a démarré
        if master_player == self.player_name:
            logger.debug("Le jeu a démarré !")
            self._message("Le jeu a démarré")
        else:
            self._message(f"Le jeu a démarré !\nC'est au tour de {master_player} de dessiner !")

        self.game_started = True
        self.widget_word_label.show()
        self.widget_word_entry.show()

        # seul le créateur peut dessiner
        if master_player == self.player_name:
            self.canvas_window.can_draw = True

    def event_end_game(self, game_name):
        logger.debug(f"game {game_name} ended")

        # Si le jeu supprimé était le jeu sélectionné il faut aussi effacer le widget de la liste des joueurs
        selected_game = self.widget_game_list.get_single_selection()
        if selected_game == game_name:
            # Clear player list
            self.widget_player_list.set_item_list([])
            self.widget_join_button.hide()

        self.widget_game_list.remove_items([game_name])

    def event_draw(self, msg):
        logger.debug(msg)
        if 'action' not in msg: return

        match msg['action']:
            case 'plot':
                self.canvas_window.draw(msg)
            case 'clear':
                self.canvas_window.clear() # JD
            case _:
                logger.error(f"event_draw called with unknown action: {msg=}")

    def event_word_found(self, winner, word, new_master):
        self.victory_sound.play()
        self._end_of_round()
        if self.player_name != winner:
            logger.debug(f"{winner} a trouvé le mot: '{word}'")
            self._message(f"{winner} a trouvé le mot: '{word}'\n"
                          f"C'est au tour de {new_master} de dessiner !")

        if new_master == self.player_name:
            self.widget_start_button.show()
        else:
            self.widget_start_button.hide()

    def event_word_not_found(self, player, word):
        logger.debug(f"{player} a proposé le mot: '{word}'")
        self.widget_proposed_words.add_items([word])

    def event_countdown_starting(self, seconds):
        self.ding_sound.play()
        logger.info(f"départ dans {seconds} secondes")

    def event_countdown_ending(self, seconds):
        logger.info(f"ending in {seconds} seconds")

    def event_countdown_playing(self, seconds):
        #logger.info(f"ending in {seconds} seconds")
        self.widget_remaining_time.set_text(f"Temps : {seconds:02}")

    def event_round_end(self, word, new_master):
        # On aurait pu fusionner avec event_word_found
        self.failure_sound.play()
        self._end_of_round()
        self._message(f"Personne n'a trouvé le mot !\n"
                      f"Il fallait deviner le mot '{word}'\n"
                      f"C'est au tour de {new_master} de dessiner !")
        if new_master == self.player_name:
            self.widget_start_button.show()
        else:
            self.widget_start_button.hide()

    def _end_of_round(self):
        self.canvas_window.can_draw = False
        self.game_started = False
        self.widget_color_button.hide()
        self.widget_clear_button.hide()
        # if self.selected_game == self.player_name:
        #     self.widget_start_button.show()
        self.widget_word_entry.set_text('')
        self.widget_word_label.hide()
        self.widget_word_entry.hide()

    def get_pseudo(self):
        #pseudo = self.widget_name_entry.get_text()[len(PSEUDO_PROMPT):]
        pseudo = self.widget_name_entry.get_text()
        if pseudo.lstrip(): # le pseudo ne peut être vide ou avec que des espaces
            self.player_name = pseudo
            try:
                self.network = Client(self.player_name, self.server_host, self.server_port)
            except Exception as e:
                self.network = None
                logger.error(e)

            if self.network:
                self.widget_name_entry.hide()
                self.widget_name_label.hide()
                self.widget_create_button.show()
                games = self.network.get_list_games()
                self.widget_game_list.set_item_list(games)
                self._set_callbacks()
                self.user_registered = True

            self._set_status_bar_text()

    def guess_word(self):
        #word = self.widget_word_entry.get_text()[len(WORD_PROMPT):]
        word = self.widget_word_entry.get_text()
        word = word.lstrip() # le mot ne peut être vide ou avec que des espaces
        if word:
            if not self.network.guess_word(word):
                logging.info(random.choice(['Et non !', "Ce n'est pas ça...", 'Mauvaise proposition']))
            else:
                logging.debug('Bravo, tu as trouvé !')
                self._message('Bravo, tu as trouvé !')

    def select_game(self, game):
        self.selected_game = game
        logging.debug(f"Le jeu sélectionné est {self.selected_game}")
        names = self.network.get_list_game_players(self.selected_game)
        logging.debug(f"Il y a {len(names)} joueurs connectés:")
        logging.debug(names)
        self.widget_player_list.set_item_list(names)

        # Si le jeu sélectionné est celui créé par le joueur: Démarrer, sinon Rejoindre
        if self.selected_game == self.player_name:
            self.widget_start_button.show()
            self.widget_join_button.hide()
        else:
            self.widget_start_button.hide()
            self.widget_join_button.show()

    def create_game(self):
        if self.network.new_game():
            self.game_created = True
            self.game = self.player_name
            self.widget_join_button.hide()
            self.widget_create_button.hide()

    def start_game(self):
        self.widget_create_button.hide()
        self.widget_start_button.hide()
        self.widget_join_button.hide()
        self.widget_leave_button.show()
        self.widget_clear_button.show()
        self.widget_color_button.show()
        self.word2guess = self.network.start_game()
        self.widget_word_entry.set_text(f"Tu dois faire deviner le mot '{self.word2guess}'")
        self.widget_word_label.show()
        self.widget_word_entry.show()
        logger.debug(f"Tu dois faire deviner le mot '{self.word2guess}'")
        self._set_status_bar_text()
        self.clear_canvas() # efface les Canvas de tous les joueurs

    def join_game(self):
        self.widget_create_button.hide()
        self.widget_join_button.hide()
        self.widget_start_button.hide()
        self.widget_leave_button.show()
        self.game = self.selected_game
        self._set_status_bar_text()
        self.network.join_game(self.selected_game)
        self._set_status_bar_text()

    def leave_game(self):
        self.widget_create_button.show()
        self.widget_join_button.show()
        self.widget_leave_button.hide()
        self.widget_clear_button.hide()
        self.widget_color_button.hide()
        self.network.leave_game(self.game)
        self.game = None
        self.game_started = False
        self.event_leave_game(self.player_name)
        self._set_status_bar_text()

    def clear_canvas(self):
        self.canvas_window.clear()
        self.network.send_clear()

    def pick_color(self):
        w, h = COLOR_WIDTH, COLOR_HEIGHT
        pygame_gui.windows.UIColourPickerDialog(rect=pygame.Rect(LEFT_MENU_WIDTH + (CANVAS_WIDTH - w) // 2, (CANVAS_HEIGHT - h) // 2, w, h),
            manager=self.manager,
            initial_colour=self.color
        )

    def set_color(self, colour):
        self.canvas_window.set_color(colour)

    def run(self):
        run = True
        clock = pygame.time.Clock()
        while run:
            time_delta = clock.tick(FPS) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.quit()
                    quit()

                try: # car il semble qu'il y ait des bugs dans pygame-gui ?
                    self.manager.process_events(event)
                except Exception as e:
                    logger.debug(e)

                # Saisie des EntryLines
                if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                    # Saisie du pseudo
                    if event.ui_element == self.widget_name_entry:
                        self.get_pseudo()

                    # Saisie d'une proposition de mot
                    if self.game_started and event.ui_element == self.widget_word_entry:
                        self.guess_word()

                # Sélection d'un jeu en cours
                if event.type == pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION and event.ui_element == self.widget_game_list:
                    self.select_game(event.text)

                # Gestion des appuis sur les boutons
                if self.user_registered and event.type == pygame_gui.UI_BUTTON_PRESSED:
                    # Création d'une nouvelle partie ?
                    if event.ui_element == self.widget_create_button and not self.game_created:
                        self.create_game()

                    # Démarrer une partie ?
                    if event.ui_element == self.widget_start_button and self.game:
                        self.start_game()

                    # Rejoindre une partie ?
                    if event.ui_element == self.widget_join_button and self.selected_game:
                        self.join_game()

                    # Quitter une partie ?
                    if event.ui_element == self.widget_leave_button and self.game:
                        self.leave_game()

                    # Efface le Canvas si c'est le joueur principal
                    if event.ui_element == self.widget_clear_button and self.canvas_window.can_draw:
                        self.clear_canvas()

                    # Choisit une couleur si c'est le joueur principal
                    if event.ui_element == self.widget_color_button and self.canvas_window.can_draw:
                        self.pick_color()

                # Choix d'une couleur
                if event.type == pygame_gui.UI_COLOUR_PICKER_COLOUR_PICKED:
                    self.set_color(event.colour)

            with display_lock:
                try:
                    self.manager.update(time_delta)
                    self.window_surface.blit(self.background, (0, 0))
                    self.manager.draw_ui(self.window_surface)
                    pygame.display.update()
                except:
                    pass

if __name__ == "__main__":
    LOG_LEVEL = 'LOG_LEVEL'

    log_level = logging.INFO
    levels = logging.getLevelNamesMapping()

    if LOG_LEVEL in os.environ:
        if os.environ[LOG_LEVEL] in levels:
            log_level = levels[os.environ[LOG_LEVEL]]

    logging.basicConfig(level=log_level)

    main = PictGame(WIDTH, HEIGHT)
    mylogger = log.Logger(log_level, main.widget_msg)
    logger = logging.getLogger()
    main.run()

# EOF
