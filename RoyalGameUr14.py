from random import randint
import dataclasses
import Reader
import threading
import sys

import socketserver as ss
import socket
import io

encoding = 'utf-8'

currout = sys.stdout
oldprint = print
def print(value):
    if sys.stdout == currout:
        oldprint(value)
    else:
        sys.stdout.write(str(value) + "\n")

currin = sys.stdin
oldinput = input
def input(prompt=""):
    if sys.stdin == currin:
        return oldinput(prompt)
    else:
        if prompt:
            print(prompt)
        return str(sys.stdin.readline())


class Game:
    intro = 'Welcome to the Royal Game of Ur!\nEnter "play" to begin, or "help" to learn how to play the game.'
    prompt = "Ur: "
    instructions = "Select piece by column (i.e. 0-13), or -1 to select a piece from the starting line."
    def __init__(self, safe_a=4, rosette_a=4, safe_b=2, rosette_b=2, combat_a=8, rosette_c=4, num_pieces=7, dice=4):
        self.board = Board(safe_a, rosette_a, safe_b, rosette_b, combat_a, rosette_c, num_pieces, dice)
        self.help = "Ur is a race between two sides. Get all your pieces from the left to the right, landing exactly on space " + str(self.board.total_spaces) + ".\nBut watch out! Spaces " + str(self.board.safe_a) + " to " + str(self.board.safe_a + self.board.combat_a - 1) + " are combat spaces.\nIf your opponent lands on your piece, and it isn't on a rosette (*), it'll have to return to the beginning.\nNot only are rosettes safe to land on, they also mean you get another roll when you land on them.\nNote: You can only skip a turn if there are absolutely no moves available. Otherwise, you must make a move, even if it's disadvantageous to you."

        self.active = False
    def play(self):
        prompt = self.instructions + "\n" + self.board.player.capitalize() + ": "
        
        print(self.intro)
        while not self.active:
            user_input = Reader.parse(input(self.prompt))
            if type(user_input) is not tuple:
                if user_input == "play":
                    self.active = True
                    self.prompt = prompt
                elif user_input == "help":
                    print(self.help)
                elif user_input == "multiplayer":
                    self.multiplayer()
                elif user_input == "quit" or user_input == "exit":
                    q = input("Are you sure you would like to quit? y/n: ")
                    if q == "y":
                        exit()
        while self.play_turn():
            continue
    def multiplayer(self):
        user_input = Reader.parse(input("Play as 'host' or 'guest'?"))
        if user_input == "host":
            self.host()
        if user_input == "guest":
            ip = input("What IP Address would you like to connect to?")
            self.guest(ip)
    def host(self):
        with ThreadedTCPServer(('', 58901), PlayerHandler) as server:
            print(f'The Royal Game of Ur server is running.')
            server.serve_forever()
            # server_thread = threading.Thread(target=server.serve_forever)
            # server_thread.daemon = True
            # server_thread.start()
            # self.guest("localhost")
    def guest(self, ip):
        try:
            client = ThreadedClient(ip)
        except Exception as e:
            print(e)
        else:
            client.main()
    def play_turn(self):
        self.prompt = self.instructions + "\n" + self.board.player.capitalize() + ": "
        self.won = self.board.player.capitalize() + " has won!\nCongratulations!!!"
        print(self.board)
        dist = self.board.die.roll()
        if not dist:
            print("You lose a turn.")
            self.board.switch_sides()
            return True
        success = False
        reroll = False
        while not success:
            wait = True
            while wait:
                wait, user_input = self.get_input()
                if user_input == 'help':
                    print(self.help)
                if user_input == 'board':
                    print(self.board)
                if user_input == 'skip':
                    if self.board.should_skip():
                        self.board.switch_sides()
                        return True
                if user_input == 'quit' or user_input == 'exit':
                    return False
            column = user_input
            piece = self.board.select_piece(column)
            success, reroll = self.board.move_by(piece, dist)
        if self.board.has_won():
            print(self.won)
            return False
        if not reroll:
            self.board.switch_sides()
        return True
    def get_input(self):
        line = Reader.parse(input(self.prompt))
        if type(line) is not tuple:
            return True, line
        if type(line[1]) is int:
            return False, line[1]
class Board:
    def __init__(self, safe_a=4, rosette_a=4, safe_b=2, rosette_b=2, combat_a=8, rosette_c=4, num_pieces=7, dice=4):
        self.safe_a = safe_a
        self.safe_b = safe_b
        self.combat_a = combat_a
        self.total_spaces = safe_a + combat_a + safe_b
        self.num_pieces = num_pieces
        
        self.die = Die(dice)
        
        self.starting_line = {'white': StartingLine('white', [Piece('white', id) for id in range(self.num_pieces)]), 'black': StartingLine('black', [Piece('black', id) for id in range(self.num_pieces)])}

        white = [None for _ in range(self.total_spaces)]
        black = [None for _ in range(self.total_spaces)]
        combat = [None for _ in range(self.total_spaces)]
        id = 0
        for n in range(safe_a):
            white[id] = Space('white', id, n + 1 == rosette_a)
            black[id] = Space('black', id, n + 1 == rosette_a)
            id += 1
        for n in range(combat_a):
            combat[id] = Space('combat', id, n + 1 == rosette_c)
            id += 1
        for n in range(safe_b):
            white[id] = Space('white', id, n + 1 == rosette_b)
            black[id] = Space('black', id, n + 1 == rosette_b)
            id += 1
        self.contents = {'white': white, 'combat': combat, 'black': black}

        self.finish_line = {'white': FinishLine('white', self.num_pieces, self.total_spaces), 'black': FinishLine('black', self.num_pieces, self.total_spaces)}
        
        self.player = 'white'
        self.won = False

    def move(self, piece, space):
        piece.location = space
        if space.rosette:
            return True, True
        return True, False
    def move_by(self, piece, number):
        # print("here.")
        if piece == None or piece.color != self.player:
            return False, False
        dest_id = piece.location.id + number
        dest = self.select_space(dest_id)
        if dest: # valid destination
            if dest.is_occupied():
                if dest.contents.color != piece.color:
                    if not dest.rosette:
                        self.remove(dest)
                        return self.move(piece, dest)
                    else:
                        return self.safe()
                else:
                    return self.invalid()
            else:
                return self.move(piece, dest)
        else:
            return False, False
    def can_move_by(self, piece, number):
        if piece == None or piece.color != self.player:
            return False
        dest_id = piece.location.id + number
        dest = self.select_space(dest_id)
        if dest: # valid destination
            if dest.is_occupied():
                if dest.contents.color != piece.color:
                    if not dest.rosette:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return True
        else:
            return False
    def safe(self):
        return self.invalid()
    def invalid(self):
        return False, False
    def select_space(self, column, player=None):
        if not player:
            player = self.player
        selected = None
        if column < 0:
            selected = self.starting_line[player]
        elif self.safe_a <= column < self.total_spaces - self.safe_b:
            selected = self.contents['combat'][column]
        elif 0 <= column < self.total_spaces:
            selected = self.contents[player][column]
        elif column == self.total_spaces:
            selected = self.finish_line[player].contents
        return selected
    def select_piece(self, column, player=None):
        if not player:
            player = self.player
        selected = None
        space = self.select_space(column, player)
        if space:
            selected = space.contents
        return selected
    def remove(self, place):
        piece = place.contents
        side = piece.color
        self.starting_line[side].contents = piece
    def make_move(self, column, dist=None):
        if dist == None:
            dist = self.die.prev
        piece = self.select_piece(column)
        if not piece:
            return False
        return self.move_by(piece, dist)
    def switch_sides(self):
        if self.player == 'white':
            self.player = 'black'
        else:
            self.player = 'white'
        return self.player
    def has_won(self):
        if self.finish_line[self.player].finished == self.num_pieces:
            self.won = True
        return self.won
        
    def should_skip(self):
        # returns True if no valid moves are available, False otherwise.
        actives = []
        for column in range(self.total_spaces):
            piece = self.select_piece(column)
            if piece:
                actives.append(piece)
        
        if len(actives) == 0 and self.starting_line[self.player].out_of_play > 0:
            return False
        
        number = self.die.prev
        for piece in actives:
            if self.can_move_by(piece, number):
                return False
        return True
        
    def __repr__(self):
        s = ''
        for color, spaces in self.contents.items():
            s += color.capitalize().center(6) + ":"
            for space in spaces:
                if space:
                    s += (str(space).center(3) + "|").center(4)
                else:
                    s += ' '.center(4)
            s += '\n'
        s += "".center(7)
        for n in range(self.total_spaces):
            s += str(n).center(4)
        return s
class FinishLine:
    def __init__(self, color, num_pieces, spaces):
        self.color = color
        self._contents = [Space(self.color, spaces, False) for _ in range(num_pieces)]
        self.finished = 0
    @property
    def contents(self):
        return self._contents
    @contents.getter
    def contents(self):
        index = self.finished
        if index >= len(self._contents):
            return None
        space = self._contents[index]
        self.finished += 1
        return space
    # @contents.setter
    # def contents(self, piece):
        # index = self.finished
        # self._contents[index].contents = piece
        # self.finished += 1
class StartingLine:
    def __init__(self, color, pieces):
        num_pieces = len(pieces)
        self.color = color
        self._contents = [Space(self.color, -1, False, piece) for piece in pieces]
        self.out_of_play = num_pieces
    @property
    def contents(self):
        return self._contents
    @contents.getter
    def contents(self):
        if self.out_of_play < 0:
            return None
        self.out_of_play -= 1
        return self._contents[self.out_of_play].contents
    @contents.setter
    def contents(self, piece):
        self._contents[self.out_of_play].contents = piece
        self.out_of_play += 1
    
class Space:
    def __init__(self, color, id, rosette, contents=None):
        self.color = color
        self.id = id
        self.rosette = rosette
        self._contents = contents
    @property
    def contents(self):
        return self._contents
    @contents.getter
    def contents(self):
        return self._contents
    @contents.setter
    def contents(self, piece):
        if piece:
            piece.location = self
        else:
            self._contents = None
    @contents.deleter
    def contents(self):
        if self._contents:
            del self._contents.location
    def is_occupied(self):
        return self.contents != None
    def __repr__(self):
        if self.contents:
            return str(self.contents)
        if self.rosette:
            return '*'
        return ' '
class Piece:
    def __init__(self, color, id):
        self.color = color
        self.id = id
        self._location = Space(color, -1, False)
    @property
    def location(self):
        return self._location
    @location.getter
    def location(self):
        return self._location
    @location.setter
    def location(self, space):
        origin = self._location
        space._contents = self
        self._location = space
        origin.contents = None
    @location.deleter
    def location(self):
        self._location._contents = None
        self._location = None
    def __repr__(self):
        s = ''
        if self.color == 'white':
            s += '\u25cb'
        if self.color == 'black':
            s += '\u25cf'
        return s + str(self.id)

class Die:
    def __init__(self, dice):
        self.dice = dice
        self.prev = None
    def roll(self):
        sum = 0
        for die in range(self.dice):
            sum += randint(0, 1)
        self.prev = sum
        print("You've rolled a " + str(sum) + "!")
        return sum
    def __repr__(self):
        return str(self.prev)
        

        
        
        


# https://cs.lmu.edu/~ray/notes/pythonnetexamples/


class ThreadedClient:
    def __init__(self, host):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, 58901))
    def listen(self):
        while True:
            data = self.sock.recv(4096).decode(encoding)
            print(data)

    def main(self):
        threading.Thread(target=self.listen).start()
        try:
            while True:
                message = currin.readline()#"input: ")
                self.sock.send(message.encode(encoding))
        except KeyboardInterrupt:
            print("Keyboard interrupt. Exiting.")

class ThreadedTCPServer(ss.ThreadingMixIn, ss.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

class PlayerHandler(ss.StreamRequestHandler):
    unpaired_game = None
    def handle(self):
        self.old_in = sys.stdin
        self.old_out = sys.stdout
        self.initialize()
        while self.game.wait:
            continue
        self.process_clients()
    def send(self, message):
        self.wfile.write((message + "\n").encode(encoding))
        # if self.opponent:
            # self.opponent.wfile.write((message + "\n").encode(encoding))
    def initialize(self):
        if not PlayerHandler.unpaired_game:
            PlayerHandler.unpaired_game = Game()
            self.game = PlayerHandler.unpaired_game
            self.color = "black"
            self.opponent = None
            self.game.player1 = self
            self.game.wait = True
        else:
            self.game = PlayerHandler.unpaired_game
            PlayerHandler.unpaired_game = None
            self.color = "white"
            self.opponent = self.game.player1
            self.opponent.opponent = self
            self.game.player2 = self
            self.game.wait = False
        self.send("Welcome, " + self.color)
    def process_clients(self):
        sys.stdout = Tee(self.wfile, self.opponent.wfile)
        self.game.continue_playing = True
        while self.game.continue_playing:
            if self.game.board.player == self.color:
                sys.stdin = self.rfile
                self.game.continue_playing = self.game.play_turn()
class Tee:
    def __init__(self, *ioputs):
        self.ioputs = ioputs
    def write(self, s):
        for ioput in self.ioputs:
            if isinstance(ioput, ss._SocketWriter):
                ioput.write(s.encode(encoding))
            else:
                ioput.write(s)
if __name__ == '__main__':
    game = Game()
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "multiplayer":
            game.guest(sys.argv[2])
        if sys.argv[1].lower() == "serve":
            game.host()
    while game.play():
        continue