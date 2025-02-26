from typing import List, Optional
from pathlib import Path
import copy
import logging

import pygame
import pygame_gui

#from event_types import UI_PAINT_PAINTING_TOOL_CHANGED
from pygame_gui import UI_BUTTON_PRESSED


DEFAULT_THICKNESS = 5
BLACK = pygame.Color(0, 0, 0)
DEFAULT_COLOR = BLACK

logger = logging.getLogger()

class EditableCanvas(pygame_gui.core.ui_element.UIElement):
    # JD: ajout de pict_game
    def __init__(self, pict_game, relative_rect, image_surface, manager, lock,
                 container=None, parent=None, object_id=None, anchors=None):
        super().__init__(relative_rect=relative_rect,
                         manager=manager,
                         container=container,
                         starting_height=1,
                         layer_thickness=1,
                         anchors=anchors)
        self._create_valid_ids(container=container,
                               parent_element=parent,
                               object_id=object_id,
                               element_id='editable_canvas')
        self.set_image(image_surface)
        self.empty_image = image_surface # pour le "clear"
        #self.active_tool = None
        self.can_draw = False
        self.clicked = False
        self.last_clicked_pos = None
        self.thickness = DEFAULT_THICKNESS
        self.color = DEFAULT_COLOR
        self.pict_game = pict_game # JD
        self.lock = lock

    #def set_active_tool(self, tool):
    #    self.active_tool = tool

    def process_event(self, event: pygame.event.Event) -> bool:
        '''Retourne True si l'événement est consommé'''
        if not self.can_draw:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Doit prendre en compte l'événement seulement si la souris est dans la fenetre et si la position a changé
            mouse_pos = self.ui_manager.get_mouse_position()
            if self.relative_rect.collidepoint(mouse_pos):
                rect = self.get_abs_rect()
                pygame.draw.circle(
                    self.image,
                    self.color,
                    (mouse_pos[0] - rect.left, mouse_pos[1] - rect.top),
                    self.thickness - 1, # radius
                    self.thickness) # thickness
                self.clicked = True
                self.last_clicked_pos = mouse_pos
                logger.debug(f"{mouse_pos[0]=},{mouse_pos[1]=},{rect.left=},{rect.top=}")
                return True

            return False

        if event.type == pygame.MOUSEBUTTONUP:
            self.clicked = False
            self.last_clicked_pos = None
            self.pict_game.network.send_plot(-1, -1, self.color)    # JD button up
            return False

        if event.type == pygame.MOUSEMOTION and self.clicked:
            # Doit prendre en compte l'événement seulement si la souris est dans la fenetre et a changé de position
            mouse_pos = self.ui_manager.get_mouse_position()
            if self.relative_rect.collidepoint(mouse_pos):
                rect = self.get_abs_rect()
                if self.last_clicked_pos:
                    pygame.draw.line(
                        self.image,
                        self.color,
                        (self.last_clicked_pos[0] - rect.left, self.last_clicked_pos[1] - rect.top),
                        (mouse_pos[0] - rect.left, mouse_pos[1] - rect.top),
                        self.thickness + 2 # thickness
                    )
                pygame.draw.circle(
                    self.image,
                    self.color,
                    (mouse_pos[0] - rect.left, mouse_pos[1] - rect.top),
                    self.thickness - 1, # radius
                    self.thickness # thickness
                )
                self.clicked = True
                if self.last_clicked_pos and mouse_pos == self.last_clicked_pos:
                    return True

                self.last_clicked_pos = mouse_pos
                logger.debug(f"{mouse_pos[0]=},{mouse_pos[1]=},{rect.left=},{rect.top=}")
                # self.color n'est pas sérailisable en JSON, on transforme en RGB
                self.pict_game.network.send_plot(mouse_pos[0] - rect.left, mouse_pos[1] - rect.top, self.color)
                return True

            return False

        return False

    def update(self, time_delta: float):
        super().update(time_delta)

    def set_image(self, new_image: Optional[pygame.surface.Surface]) -> None:
        self._set_image(new_image)

    def clear(self):
        #self.set_image(copy.copy(self.empty_image))
        self.set_image(self.empty_image)

    def set_color(self, color):
        self.color = color

    # JD
    def draw(self, dict_msg):
        with self.lock:
            '''Drawing event handling'''
            x = dict_msg['x']
            y = dict_msg['y']
            color = dict_msg['color']
            rect = self.get_abs_rect()

            if x == -1 and y == -1: # Pen is up
                self.last_clicked_pos = None
                return 

            x, y = x - rect.left, y - rect.top

            if self.last_clicked_pos:
                pygame.draw.line(
                    self.image,
                    color,
                    #(self.last_clicked_pos[0] + rect.left, self.last_clicked_pos[1] + rect.top),
                    (self.last_clicked_pos[0], self.last_clicked_pos[1]),
                    (x + rect.left, y + rect.top),
                    self.thickness + 2 # thickness
                )
            pygame.draw.circle(
                self.image,
                color,
                (x + rect.left, y + rect.top),
                self.thickness - 1, # radius
                self.thickness # thickness
            )
            self.last_clicked_pos = (x + rect.left, y + rect.top)

