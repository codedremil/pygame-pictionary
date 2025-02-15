'''
Implémente l'interface graphique du jeu
'''
import sys
import os
import logging
import log # JD
import pygame
import pygame_gui

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, '..', 'common'))

from client import Client
from protocol import Protocol
from settings import HOST, PORT
from editable_canvas import EditableCanvas

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG = BLACK
FPS = 30
WIDTH = 800
HEIGHT = 600

# Dimensions des widgets
SPACING = 3
LEFT_MENU_WIDTH = 100
LABEL_HEIGHT = 30
GAME_LIST_HEIGHT = 100
PLAYER_LIST_HEIGHT = 140
STATUS_BAR_HEIGHT = 20
MSGBOX_WIDTH = WIDTH
MSGBOX_HEIGHT = 100
CANVAS_WIDTH = WIDTH - LEFT_MENU_WIDTH - 2 * SPACING
CANVAS_HEIGHT = HEIGHT - STATUS_BAR_HEIGHT - MSGBOX_HEIGHT - 2 * SPACING
BUTTON_WIDTH = 50
BUTTON_HEIGHT = 20
TOOLBAR_HEIGHT = 300

logger = None


class PictGame:
    PSEUDO_PROMPT = ' Indique ton pseudo: '

    def __init__(self, width, height):
        pygame.init()
        pygame.font.init()
        #pygame.mixer.init()
        pygame.mixer.quit()
        pygame.display.set_caption('Pictionary en réseau')

        self.width = width 
        self.height = height
        self.window_surface = pygame.display.set_mode((self.width, self.height))
        self.player_name = ""
        # self.waiting = False
        self.network = None
        self.game = None
        self.status_bar = ""
        self.name_font = pygame.font.SysFont("comicsans", 80)
        self.title_font = pygame.font.SysFont("comicsans", 120)
        self.enter_font = pygame.font.SysFont("comicsans", 60)
        self._build_interface()

    def _build_interface(self):
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(pygame.Color(BG))

        # Création du Manager
        self.manager = pygame_gui.UIManager((self.width, self.height), theme_path="gui.json")

        # Pour la saisie du pseudo
        w, h = 300, 50 # centré (pas beau !)
        self.widget_name_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(((self.width - w) // 2, (self.height - h) // 2), (w, h)),
            manager=self.manager,
            initial_text=PictGame.PSEUDO_PROMPT
        )
        self.widget_name_entry.change_layer(10)

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
            text='Liste des joueurs :',
        )

        w, h = LEFT_MENU_WIDTH, PLAYER_LIST_HEIGHT # collé en haut à gauche
        self.widget_player_list = pygame_gui.elements.UISelectionList(
            #relative_rect=pygame.Rect((0, LABEL_HEIGHT), (w, h)),
            relative_rect=pygame.Rect((0, 0), (w, h)),
            manager=self.manager,
            anchors={'top': 'top', 'top_target': label},
            item_list=[],
        )

        # Pour créer et démarrer un jeu

        # Pour joindre ou quitter un jeu

        # Pour proposer un mot

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
            relative_rect=canvas_window_rect,
            manager=self.manager,
            image_surface=new_canvas
        )

    def _set_callbacks(self):
        self.network.set_callback(Protocol.EVENT_NEW_GAME, self.event_new_game)

    def _get_status_bar_text(self):
        connected = "connecté" if self.network else "déconnecté"
        game_in_progress = self.game if self.game else "aucun"
        return f"Serveur: {connected}   Pseudo: {self.player_name}   Jeu: {game_in_progress}"

    def event_new_game(self, game_name):
        # Ajoute le jeu dans la liste
        self.widget_game_list.add_items([game_name])

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

                self.manager.process_events(event)

                # Saisie du pseudo
                if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED and event.ui_element == self.widget_name_entry:
                    text = self.widget_name_entry.get_text()[len(PictGame.PSEUDO_PROMPT):]
                    if text.lstrip(): # le pseudo ne peut être vide ou avec que des espaces
                        self.player_name = text
                        try:
                            self.network = Client(self.player_name, HOST, PORT)
                        except Exception as e:
                            self.network = None
                            logger.error(e)

                        if self.network:
                            self.widget_name_entry.hide() # JD
                            games = self.network.get_list_games()
                            self.widget_game_list.set_item_list(games)
                            self._set_callbacks()
                            self.canvas_window.can_draw = True

                        self.widget_server_status.set_text(self._get_status_bar_text())

                # Sélection d'un jeu en cours
                if event.type == pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION and event.ui_element == self.widget_game_list:
                    game_name = event.text
                    logging.debug(f"Choosen game is {game_name}")
                    names = self.network.get_list_game_players(game_name)
                    logging.debug(f"Il y a {len(names)} joueurs connectés:")
                    logging.debug(names)
                    self.widget_player_list.set_item_list(names)

            self.manager.update(time_delta)
            self.window_surface.blit(self.background, (0, 0))
            self.manager.draw_ui(self.window_surface)
            pygame.display.update()


if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    main = PictGame(WIDTH, HEIGHT)
    mylogger = log.Logger(main.widget_msg) # JD
    logger = logging.getLogger()
    main.run()

# EOF
