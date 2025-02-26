import threading


class Game:
    def __init__(self, player):
        '''le nom du jeu est le nom du joueur'''
        self.name = player.name
        self.word_to_guess = None
        self.players = []
        self.lock_players = threading.Lock()
        self.add_player(player)

    def add_player(self, player):
        # vérifie que le joueur ne s'enregistre pas 2 fois
        with self.lock_players:
            if player.name not in self.players:
                self.players.append(player.name)
                player.set_game(self)

    def remove_player(self, player):
        with self.lock_players:
            if player.name in self.players:
                self.players.remove(player.name)

            player.set_game(None)

