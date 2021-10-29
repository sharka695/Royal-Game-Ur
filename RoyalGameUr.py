#     Copyright 2021 sharka695
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as published
#     by the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from random import randint
import dataclasses
import Reader
import threading
import sys
from ANSI import ANSI

import subprocess
import shutil

import os
import socketserver as ss
import socket
import io

from contextlib import closing
from time import sleep

style = ANSI.background_white + ANSI.foreground_black + ANSI.not_blinking

encoding = 'utf-8'

currout = sys.stdout
oldprint = print
fill_style_to_end = "\x1b[K"
def print(value):
    if sys.stdout == currout:
        oldprint(value, end='\n' + fill_style_to_end)
    else:
        sys.stdout.write(str(value) + "\n" + fill_style_to_end)

currin = sys.stdin
oldinput = input
def input(prompt=""):
    if sys.stdin == currin:
        return oldinput(prompt + fill_style_to_end)
    else:
        if prompt:
            print(prompt + fill_style_to_end)
        return str(sys.stdin.readline().decode(encoding)) # + fill_style_to_end

class Game:
    print(style)
    intro = 'Copyright 2021 sharka695\n\nWelcome to the Royal Game of Ur!\nEnter "play" to begin, or "help" to learn how to play the game.\nEnter "multiplayer" to play online.\nEnter "ai" to play against an artificial intelligence.'
    prompt = "Ur: "
    instructions = "Select piece by column (i.e. 0-13), or\nEnter '-1' to select a piece from the starting line."
    def __init__(self, safe_a=4, rosette_a=4, safe_b=2, rosette_b=2, combat_a=8, rosette_c=4, num_pieces=7, dice=4):
        self.board = Board(safe_a, rosette_a, safe_b, rosette_b, combat_a, rosette_c, num_pieces, dice)
        self.help = "Ur is a race between two sides. Get all your pieces from the left to the right, landing exactly on space " + str(self.board.total_spaces) + fill_style_to_end + ".\nBut watch out! Spaces " + str(self.board.safe_a) + " to " + str(self.board.safe_a + self.board.combat_a - 1) + " are combat spaces." + fill_style_to_end + "\nIf your opponent lands on your piece, and it isn't on a rosette (*), it'll have to return to the beginning." + fill_style_to_end + "\nNot only are rosettes safe to land on, they also mean you get another roll when you land on them." + fill_style_to_end + "\nNote: You can only skip a turn if there are absolutely no moves available. Otherwise, you must make a move, even if it's disadvantageous to you." + fill_style_to_end

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
                elif user_input == "ai":
                    self.ai()
                    self.reset()
                elif user_input == "quit" or user_input == "exit":
                    q = input(ANSI.foreground_red + "Are you sure you would like to quit? y/n: " + style)
                    if q == "y":
                        return
        while self.play_turn():
            continue
        self.active = False
        self.reset()
        self.play()
    def reset(self):
        self.board = Board()

    def multiplayer(self):
        user_input = Reader.parse(input("Play as 'host' or 'guest' (or 'hostplayer' [experimental])? "))
        if user_input == "host":
            self.host()
        if user_input == "hostplayer":
            self.host_player()
        if user_input == "guest":
            ip = input("What IP Address would you like to connect to? ")
            self.guest(ip)
    def host(self, port=1025):
        with ThreadedTCPServer(('', port), PlayerHandler) as server:
            print('The Royal Game of Ur server is running.')
            server.serve_forever()
            # server_thread = threading.Thread(target=server.serve_forever)
            # server_thread.daemon = True
            # server_thread.start()
            # self.guest("localhost")
    def host_player(self):
        # def check_socket(host='', port=1025):
        #     # https://stackoverflow.com/a/45217844
        #     with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        #         return sock.connect_ex((host, port)) == 0
        # def wait_for_socket(host='', port=1025, retries=10, wait=10):
        #     while not check_socket(host, port) and retries > 0:
        #         sleep(wait)
        #         retries -= 1
        #     return retries <= 0
        # server.serve_forever()
        # server_thread = threading.Thread(target=server.serve_forever)
        # server_thread.daemon = True
        # server_thread.start()
        if getattr(sys, 'frozen', False):
            serve = [sys.executable, "serve"]
        else:
            serve = [sys.executable, os.path.basename(__file__), "serve"]
        print("Executing '" + " ".join(serve) + "' as daemon.")
        try:
            proc = subprocess.Popen(serve)
            print('Giving the server time to start. Please be patient.')
            # if wait_for_socket():
            #     raise Exception("Apparently, The Royal Game of Ur server actually isn't running. Please try again.")
            sleep(10)
            print('The Royal Game of Ur server is running.')
            self.guest("localhost")
        except Exception as e:
            proc.kill()
            raise
    def guest(self, ip):
        print(ANSI.erase_entire_screen)
        try:
            client = ThreadedClient(ip)
        except ConnectionRefusedError as e:
            print(e)
            return
        else:
            client.main()
    def ai(self):
        playing = True
        while playing:
            if self.board.player == "white":
                playing = self.play_turn()
            else:
                playing = self.play_ai()
    def play_ai(self):
        """ Thanks for your contribution, Hirudan:
            "My algorithm would be kinda like this:
            - if I can score a piece, do that
            - if I can bonk an opponent's piece, do that
            - if I can hit a rosette, do that
            - if I can develop a new piece, do that
            - otherwise, advance pieces in this order:
            -- those that prevent me from developing a new piece
            -- whichever one is furthest along"
        """
        if self.board.player == "white":
            coloration = ANSI.background_white + ANSI.foreground_black
        else:
            coloration = ANSI.background_black + ANSI.foreground_white
        self.prompt = self.instructions + "\n" + coloration +  self.board.player.capitalize() + ": " + style
        self.won = ANSI.blinking + self.board.player.capitalize() + " has won!\nCongratulations!!!\U0001f389" + style
        print(self.board)
        dist = self.board.die.roll()
        rolled = ANSI.foreground_red + self.board.player + " rolled a " + str(dist) + "!" + style
        print(rolled)
        if not dist:
            print(coloration + self.board.player + style + " loses a turn.")
            self.board.switch_sides()
            return True
        success = False
        reroll = False
        while not success:
            wait = True
            while wait:
                # wait, user_input = self.get_input()
                wait, user_input = self.get_ai_input()
                if user_input == 'help':
                    print(self.help)
                if user_input == 'board':
                    print(self.board)
                if user_input == 'roll':
                    print(rolled)
                if user_input == 'skip':
                    if self.board.should_skip():
                        self.board.switch_sides()
                        print("Skipped!")
                        return True
                    else:
                        print("You can only skip a turn if there are absolutely no moves available.\nOtherwise, you must make a move, even if it's disadvantageous to you.")
                # if user_input == 'quit' or user_input == 'exit':
                #     return False
                if user_input == "quit" or user_input == "exit":
                    q = input(ANSI.foreground_red + "Are you sure you would like to quit? y/n: " + style)
                    if q == "y":
                        return False
            column = user_input
            piece = self.board.select_piece(column)
            success, reroll = self.board.move_by(piece, dist)
        if self.board.has_won():
            print(self.won)
            return False
        if not reroll:
            self.board.switch_sides()
        print(ANSI.erase_entire_screen)
        return True
    def get_ai_input(self):
        line = Reader.parse(self.board.ai_input())
        if type(line) is not tuple:
            return True, line
        if type(line[1]) is int:
            return False, line[1]
    def play_turn(self):
        if self.board.player == "white":
            coloration = ANSI.background_white + ANSI.foreground_black
        else:
            coloration = ANSI.background_black + ANSI.foreground_white
        self.prompt = self.instructions + "\n" + coloration +  self.board.player.capitalize() + ": " + style
        self.won = ANSI.blinking + self.board.player.capitalize() + " has won!\nCongratulations!!!\U0001f389" + style
        print(self.board)
        dist = self.board.die.roll()
        rolled = ANSI.foreground_red + "You've rolled a " + str(dist) + "!" + style
        print(rolled)
        if not dist:
            print(coloration + self.board.player + style + " loses a turn.")
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
                if user_input == 'roll':
                    print(rolled)
                if user_input == 'skip':
                    if self.board.should_skip():
                        self.board.switch_sides()
                        print("Skipped!")
                        return True
                    else:
                        print("You can only skip a turn if there are absolutely no moves available.\nOtherwise, you must make a move, even if it's disadvantageous to you.")
                # if user_input == 'quit' or user_input == 'exit':
                #     return False
                if user_input == "quit" or user_input == "exit":
                    q = input(ANSI.foreground_red + "Are you sure you would like to quit? y/n: " + style)
                    if q == "y":
                        return False
            column = user_input
            piece = self.board.select_piece(column)
            success, reroll = self.board.move_by(piece, dist)
        if self.board.has_won():
            print(self.won)
            return False
        if not reroll:
            self.board.switch_sides()
        print(ANSI.erase_entire_screen)
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

        self.dice = dice
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

    def move(self, piece, dest_id):
        # # origin = piece.location
        # self.select_space(piece.location.id, piece.color).contents = None
        # # destination.contents = piece
        # self.select_space(destination.id, piece.color).contents = piece
        # piece.location = destination
        # # origin.contents = None
        self.select_space(piece.location.id, piece.color).contents = None
        self.select_space(dest_id, piece.color).contents = piece
        piece.location = self.select_space(dest_id, piece.color)
        if self.select_space(dest_id, piece.color).rosette:
            return True, True
        return True, False
        # if destination.rosette:
        #     return True, True
        # return True, False
    # def move_by(self, piece, number):
    #     if piece == None or piece.color != self.player:
    #         return False, False
    #     dest_id = piece.location.id + number
    #     dest = self.select_space(dest_id)
    #     if dest: # valid destination
    #         if dest.is_occupied():
    #             if dest.contents.color != piece.color:
    #                 if not dest.rosette:
    #                     self.remove(dest)
    #                     return self.move(piece, dest)
    #                 else:
    #                     return self.safe()
    #             else:
    #                 return self.invalid()
    #         else:
    #             return self.move(piece, dest)
    #     else:
    #         return False, False

    def move_by(self, piece, number):
        if piece == None or piece.color != self.player:
            return False, False
        dest_id = piece.location.id + number
        dest = self.select_space(dest_id)
        if not dest: # invalid destination
            return False, False
        if not dest.is_occupied(): # open destination
            # return self.move(piece, dest)
            return self.move(piece, dest_id)
        if dest.contents.color == piece.color: # can't take own piece
            return self.invalid()
        if dest.rosette: # destination is occupied by opponent
            return self.safe()
        self.remove(dest)
        # return self.move(piece, dest)
        return self.move(piece, dest_id)

    def can_move_by(self, piece, number):
        if piece == None or piece.color != self.player:
            return False
        dest_id = piece.location.id + number
        dest = self.select_space(dest_id)
        # if dest: # valid destination
        #     if dest.is_occupied():
        #         if dest.contents.color != piece.color:
        #             if not dest.rosette:
        #                 return True
        #             else:
        #                 return False
        #         else:
        #             return False
        #     else:
        #         return True
        # else:
        #     return False
        if not dest: # invalid destination
            return False
        if not dest.is_occupied(): # open destination
            return True
        if dest.contents.color == piece.color: # can't take own piece
            return False
        return not dest.rosette # destination is occupied by opponent


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
            # selected = self.starting_line[player].pseudo_space
        elif self.safe_a <= column < self.total_spaces - self.safe_b:
            selected = self.contents['combat'][column]
        elif 0 <= column < self.total_spaces:
            selected = self.contents[player][column]
        elif column == self.total_spaces:
            selected = self.finish_line[player]#.contents
        return selected
    def select_piece(self, column, player=None):
        if not player:
            player = self.player
        selected = None
        space = self.select_space(column, player)
        if space:
            selected = space.contents
        return selected
    # def remove(self, place):
    #     piece = place.contents
    #     side = piece.color
    #     self.starting_line[side].contents = piece
    #     # self.starting_line[side].pseudo_space = piece
    #     place.contents = None
    def remove(self, place):
        piece = place.contents
        self.move(piece, -1)
    def make_move(self, column, dist=None):
        if dist == None:
            dist = self.die.prev
        piece = self.select_piece(column)
        if not piece:
            return False
        return self.move_by(piece, dist)
    # def switch_sides(self):
    #     if self.player == 'white':
    #         self.player = 'black'
    #     else:
    #         self.player = 'white'
    #     return self.player
    def switch_sides(self):
        self.player = self.get_opponent(self.player)
        return self.player
    def get_opponent(self, side):
        if side == 'white':
            return 'black'
        else:
            return 'white'
    def has_won(self):
        if self.finish_line[self.player].finished == self.num_pieces:
            self.won = True
        return self.won

    def should_skip(self):
        # returns True if no valid moves are available, False otherwise.
        dist = self.die.prev
        for column in range(-1, self.total_spaces):
            piece = self.select_piece(column)
            if piece and (piece.color == self.player) and self.can_move_by(piece, dist):
                return False
        return True

    def __repr__(self):
        s = '' #ANSI.background_white + ANSI.foreground_black#''
        for color, line in self.starting_line.items():
            s += str(line) + '\n'
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
        s += '\n'
        for color, line in self.finish_line.items():
            s+= str(line) + '\n'
        return s + style

##############################################################################
#   AI TOOLS:
#   Thanks for your contribution, Hirudan:
#   "My algorithm would be kinda like this:
#   - if I can score a piece, do that
#   - if I can bonk an opponent's piece, do that
#   - if I can hit a rosette, do that
#   - if I can develop a new piece, do that
#   - otherwise, advance pieces in this order:
#   -- those that prevent me from developing a new piece
#   -- whichever one is furthest along"
##############################################################################
    def ai_input(self):
        actives = []
        dist = self.die.prev
        for column in range(self.total_spaces - 1, -2, -1):
            piece = self.select_piece(column)
            if piece and (piece.color == self.player) and self.can_move_by(piece, dist):
                actives.append(piece)
                print(piece.location.id)

        if not actives:
            return "skip"
        for piece in actives:
            if self.can_score(piece, dist):
                return str(piece.location.id)
        for piece in actives:
            if self.can_take(piece, dist):
                return str(piece.location.id)
        for piece in actives:
            if self.can_rosette(piece, dist):
                return str(piece.location.id)
        for piece in actives:
            if self.can_start_a_piece(piece, dist):
                return str(piece.location.id)
        # for piece in actives:
        #     if self.can_move_by(piece, dist):
        #         return str(piece.location.id)
        # return "skip"
        return str(actives[0].location.id)

    def can_score(self, piece, dist):
        dest_id = piece.location.id + dist
        return dest_id == self.total_spaces

    def can_take(self, piece, dist):
        dest_id = piece.location.id + dist
        destination = self.select_space(dest_id)
        return destination.is_occupied() and (destination.contents.color != piece.color) and not destination.rosette

    def can_rosette(self, piece, dist):
        dest_id = piece.location.id + dist
        destination = self.select_space(dest_id)
        return not destination.is_occupied() and destination.rosette

    def can_start_a_piece(self, piece, dist):
        return piece.location.id == -1

    def can_get_hit(self, piece, dist):
        dest_id = piece.location.id + dist
        destination = self.select_space(dest_id)
        opponent = get_opponent(piece.color)
        for dist in range(1, self.dice + 1):
            space_in_attacking_range = self.select_space(dest_id - dist, opponent)
            if space_in_attacking_range.is_occupied():
                return True
        return False

class FinishLine:
    # def __init__(self, color, num_pieces, spaces):
    #     self.color = color
    #     self._contents = [Space(self.color, spaces, False) for _ in range(num_pieces)]
    #     self.finished = 0
    # @property
    # def contents(self):
    #     return self._contents
    # @contents.getter
    # def contents(self):
    #     index = self.finished
    #     if index >= len(self._contents):
    #         return None
    #     space = self._contents[index]
    #     self.finished += 1
    #     return space
    def __init__(self, color, num_pieces, spaces):
        self.color = color
        self._pseudo_space = [Space(self.color, spaces, False) for _ in range(num_pieces)]
        self.finished = 0
        self.id = -1
        self.rosette = False
    def is_occupied(self):
        return False
    @property
    def pseudo_space(self):
        return self._pseudo_space[self.finished - 1]
    @property
    def contents(self):
        return self.pseudo_space.contents
    @contents.getter
    def contents(self):
        return self.pseudo_space.contents
    @contents.setter
    def contents(self, piece):
        if piece:
            self.finished += 1
        self.pseudo_space.contents = piece
        if not piece:
            self.finished -= 1
    @contents.deleter
    def contents(self):
        del self.pseudo_space.contents
        self.finished -= 1
    def __repr__(self):
        s = "<"
        for space in self._pseudo_space:
            s += str(space).center(2)
        return s + ">"

# class StartingLine:
#     def __init__(self, color, pieces):
#         self.color = color
#         self._contents = [Space(self.color, -1, False, piece) for piece in pieces]
#         self.out_of_play = len(pieces)
#     @property
#     def contents(self):
#         return self._contents
#     @contents.getter
#     def contents(self):
#         if self.out_of_play < 0:
#             print("out of play:" + str(self.out_of_play))
#             return None
#         self.out_of_play -= 1
#         print("out of play:" + str(self.out_of_play))
#         return self._contents[self.out_of_play].contents
#     @contents.setter
#     def contents(self, piece):
#         self._contents[self.out_of_play].contents = piece
#         self.out_of_play += 1
#         print("out of play:" + str(self.out_of_play))

# class StartingLine:
#     def __init__(self, color, pieces):
#         self.color = color
#         self._contents = [Space(self.color, -1, False, piece) for piece in pieces]
#         self.out_of_play = len(pieces) - 1
#     @property
#     def contents(self):
#         return self._contents
#     @contents.getter
#     def contents(self):
#         if self.out_of_play < 0:
#             return None
#         # self.out_of_play -= 1
#         print(self.color + " out of play: " + str(self.out_of_play))
#         return self._contents[self.out_of_play].contents
#     @contents.setter
#     def contents(self, piece):
#         if piece.location.id < 0:
#             self.out_of_play -= 1
#         else:
#             self.out_of_play += 1
#         print(self.color + " out of play: " + str(self.out_of_play))
#         self._contents[self.out_of_play].contents = piece

class StartingLine:
    def __init__(self, color, pieces):
        self.color = color
        self._pseudo_space = [Space(self.color, -1, False, piece) for piece in pieces]
        self.out_of_play = len(pieces)
        self.id = -1
        self.rosette = False
    def is_occupied(self):
        return False
    @property
    def pseudo_space(self):
        return self._pseudo_space[self.out_of_play - 1]
    @property
    def contents(self):
        return self.pseudo_space.contents
    @contents.getter
    def contents(self):
        return self.pseudo_space.contents
    @contents.setter
    def contents(self, piece):
        if piece:
            self.out_of_play += 1
        self.pseudo_space.contents = piece
        if not piece:
            self.out_of_play -= 1
    @contents.deleter
    def contents(self):
        del self.pseudo_space.contents
        self.out_of_play -= 1
    def __repr__(self):
        s = "["
        for space in self._pseudo_space:
            s += str(space).center(2)
        return s + "]" # + " pieces out of play: " + str(self.out_of_play)

class Space:
    def __init__(self, color, id, rosette, contents=None):
        self.color = color
        self.id = id
        self.rosette = rosette
        self.contents = contents

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
        self.location = Space(color, -1, False)

    def __repr__(self):
        s = ''
        if self.color == 'white':
            s += '\u25cb'
        if self.color == 'black':
            s += '\u25cf'
        return (s + " " + str(self.id)) #.center(4)

class Die:
    def __init__(self, dice):
        self.dice = dice
        self.prev = None
    def roll(self):
        sum = 0
        for die in range(self.dice):
            sum += randint(0, 1)
        self.prev = sum
        # print("You've rolled a " + str(sum) + "!")
        return sum
    def __repr__(self):
        return str(self.prev)

# https://cs.lmu.edu/~ray/notes/pythonnetexamples/
class ThreadedClient:
    def __init__(self, host, port=1025):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
    def listen(self):
        while True:
            data = self.sock.recv(4096).decode(encoding)
            # data = data.strip()
            # if data:
            #     print(ANSI.erase_entire_screen)
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
            coloration = ANSI.background_black + ANSI.foreground_white
        else:
            self.game = PlayerHandler.unpaired_game
            PlayerHandler.unpaired_game = None
            self.color = "white"
            self.opponent = self.game.player1
            self.opponent.opponent = self
            self.game.player2 = self
            self.game.wait = False
            coloration = ANSI.background_white + ANSI.foreground_black
        self.send("Source code available at https://github.com/sharka695/Royal-Game-Ur")
        self.send("Welcome, " + ANSI.blinking + coloration + self.color + style)
    def process_clients(self):
        sys.stdout = Tee(self.wfile, self.opponent.wfile)
        self.game.continue_playing = True
        while self.game.continue_playing:
            if self.game.board.player == self.color:
                sys.stdin = self.rfile
                self.game.continue_playing = self.game.play_turn()
                # self.opponent.send(str(self.game.board))

class Tee:
    def __init__(self, *inputs):
        self.inputs = inputs
    def write(self, s):
        for input in self.inputs:
            if isinstance(input, ss._SocketWriter):
                input.write(s.encode(encoding))
            else:
                input.write(s)

if __name__ == '__main__':
    print(ANSI.erase_entire_screen)
    game = Game()
    try:
        if len(sys.argv) > 1:
            if sys.argv[1].lower() == "multiplayer":
                game.guest(sys.argv[2])
            if sys.argv[1].lower() == "serve":
                game.host()
        while game.play():
            continue
    except Exception as e:
        print(ANSI.normal)
        print(ANSI.erase_entire_screen)
        raise
    else:
        print(ANSI.normal)
        print(ANSI.erase_entire_screen)
