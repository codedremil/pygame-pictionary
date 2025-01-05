class Player:
    def __init__(self, name, proto):
        self.name = name
        self.cmd_channel = proto
        self.event_channel = None
        self.game = None

    def set_event_channel(self, proto):
        self.event_channel = proto

    def set_game(self, game):
        self.game = game
