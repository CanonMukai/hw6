#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import json
import logging
import random
import webapp2
import time
import sys

# Reads json description of the board and provides simple interface.
class Game:
	# Takes json or a board directly.
	def __init__(self, body=None, board=None):
                if body:
		        game = json.loads(body)
                        self._board = game["board"]
                else:
                        self._board = board

	# Returns piece on the board.
	# 0 for no pieces, 1 for player 1, 2 for player 2.
	# None for coordinate out of scope.
	def Pos(self, x, y):
		return Pos(self._board["Pieces"], x, y)

	# Returns who plays next.
	def Next(self):
		return self._board["Next"]

	# Returns the array of valid moves for next player.
	# Each move is a dict
	#   "Where": [x,y]
	#   "As": player number
	def ValidMoves(self):
                moves = []
                for y in xrange(1,9):
                        for x in xrange(1,9):
                                move = {"Where": [x,y],
                                        "As": self.Next()}
                                if self.NextBoardPosition(move):
                                        moves.append(move)
                return moves

	# Helper function of NextBoardPosition.  It looks towards
	# (delta_x, delta_y) direction for one of our own pieces and
	# flips pieces in between if the move is valid. Returns True
	# if pieces are captured in this direction, False otherwise.
	def __UpdateBoardDirection(self, new_board, x, y, delta_x, delta_y):
		player = self.Next()
		opponent = 3 - player
		look_x = x + delta_x
		look_y = y + delta_y
		flip_list = []
		while Pos(new_board, look_x, look_y) == opponent:
			flip_list.append([look_x, look_y])
			look_x += delta_x
			look_y += delta_y
		if Pos(new_board, look_x, look_y) == player and len(flip_list) > 0:
                        # there's a continuous line of our opponents
                        # pieces between our own pieces at
                        # [look_x,look_y] and the newly placed one at
                        # [x,y], making it a legal move.
			SetPos(new_board, x, y, player)
			for flip_move in flip_list:
				flip_x = flip_move[0]
				flip_y = flip_move[1]
				SetPos(new_board, flip_x, flip_y, player)
                        return True
                return False

	# Takes a move dict and return the new Game state after that move.
	# Returns None if the move itself is invalid.
	def NextBoardPosition(self, move):
		x = move["Where"][0]
		y = move["Where"][1]
                if self.Pos(x, y) != 0:
                        # x,y is already occupied.
                        return None
		new_board = copy.deepcopy(self._board)
                pieces = new_board["Pieces"]

		if not (self.__UpdateBoardDirection(pieces, x, y, 1, 0)
                        | self.__UpdateBoardDirection(pieces, x, y, 0, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, 0)
		        | self.__UpdateBoardDirection(pieces, x, y, 0, -1)
		        | self.__UpdateBoardDirection(pieces, x, y, 1, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, 1, -1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, -1)):
                        # Nothing was captured. Move is invalid.
                        return None
                
                # Something was captured. Move is valid.
                new_board["Next"] = 3 - self.Next()
		return Game(board=new_board)

# Returns piece on the board.
# 0 for no pieces, 1 for player 1, 2 for player 2.
# None for coordinate out of scope.
#
# Pos and SetPos takes care of converting coordinate from 1-indexed to
# 0-indexed that is actually used in the underlying arrays.
def Pos(board, x, y):
	if 1 <= x and x <= 8 and 1 <= y and y <= 8:
		return board[y-1][x-1]
	return None

# Set piece on the board at (x,y) coordinate
def SetPos(board, x, y, piece):
	if x < 1 or 8 < x or y < 1 or 8 < y or piece not in [0,1,2]:
		return False
	board[y-1][x-1] = piece

# Debug function to pretty print the array representation of board.
def PrettyPrint(board, nl="<br>"):
	s = ""
	for row in board:
		for piece in row:
			s += str(piece)
		s += nl
	return s

def PrettyMove(move):
	m = move["Where"]
	return '%s%d' % (chr(ord('A') + m[0] - 1), m[1])

class MainHandler(webapp2.RequestHandler):
    # Handling GET request, just for debugging purposes.
    # If you open this handler directly, it will show you the
    # HTML form here and let you copy-paste some game's JSON
    # here for testing.
    def get(self):
        if not self.request.get('json'):
          self.response.write("""
<body><form method=get>
Paste JSON here:<p/><textarea name=json cols=80 rows=24></textarea>
<p/><input type=submit>
</form>
</body>
""")
          return
        else:
          g = Game(self.request.get('json'))
          self.pickMove(g)

    def post(self):
    	# Reads JSON representation of the board and store as the object.
    	g = Game(self.request.body)
        # Do the picking of a move and print the result.
        self.pickMove(g)


    def pickMove(self, g):
    	# Gets all valid moves.
    	valid_moves = g.ValidMoves()
    	if len(valid_moves) == 0:
    		# Passes if no valid moves.
    		self.response.write("PASS")
    	else:
    		# Chooses a valid move randomly if available.
                # TO STEP STUDENTS:
                # You'll probably want to change how this works, to do something
                # more clever than just picking a random move.

                start = time.time()
                move = MinMax(g._board["Pieces"], g.Next(), valid_moves, 1, g, start)
    		self.response.write(PrettyMove(move))  # E3とか出してる

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)


def point_of_board(board, as1or2):
        player1point = 0
        player2point = 0
        for x in range(1, 9):
                for y in range(1, 9):
                        if board[y-1][x-1] == 1:
                                player1point += pos_point[y-1][x-1]
                        elif board[x-1][y-1] == 2:
                                player2point += pos_point[y-1][x-1]
        if as1or2 == 1:
                return player1point - player2point
        else:
                return player2point - player1point


def MinMax(board, as1or2, valid_moves, depth, g, start):
        now = time.time()
        #if now - start > 10.0:
        #        return
        moves_and_points = {}
        for move in valid_moves:
                board1 = board
                g1 = g
                g1.NextBoardPosition(move)
                next_valid_moves = g1.ValidMoves()
                if len(next_valid_moves) > 0:
                        if depth == 4:
                                point = point_of_board(g1._board["Pieces"], as1or2)
                        else:
                                point = MinMax(g1._board["Pieces"], as1or2, next_valid_moves, depth+1, g1, start)
                        moves_and_points[point] = move
                else:
                        if depth == 1:
                                return -10000
                        else:
                                return 10000

        if depth == 1:
                max_point = max_of_points(moves_and_points)
                return moves_and_points[max_point]
        elif depth % 2 == 1:
                max_point = max_of_points(moves_and_points)
                return max_point
        else:
                min_point = min_of_points(moves_and_points)
                return min_point


"""
def MinMax2(g, as1or2):
        depth_moves = {} #{1:{move1: [g, -3, move], move2: [move]},2:{move},3:[],...}
        
        rest_time = 10
        while rest_time > 4.0:
                start = time.time()
                depth = 1
                valid_moves = g.ValidMoves()
                for move in valid_moves:
                        g1 = g
                        g1.NextBoardPosition(move)
                        point = point_of_board(g1, as1or2)
                        depth_moves[depth][move] = [g1, point, move]
"""

def max_of_points(points_and_moves):
        max_point = -1000
        for point in points_and_moves:
                if point > max_point:
                        max_point = point
        return max_point

def min_of_points(points_and_moves):
        min_point = 1000
        for point in points_and_moves:
                if point < min_point:
                        min_point = point
        return min_point

"""
pos_point = [
        [120, -20, 20, 5, 5, 20, -20, 120],
        [-20, 40, -5, -5, -5, -5, -40, -20],
        [20, -5, 15, 3, 3, 15, -5, 20],
        [5, -5, 3, 3, 3, 3, -5, 5],
        [5, -5, 3, 3, 3, 3, -5, 5],
        [20, -5, 15, 3, 3, 15, -5, 20],
        [-20, 40, -5, -5, -5, -5, -40, -20],
        [120, -20, 20, 5, 5, 20, -20, 120]
        ]
"""
pos_point = [
        [ 30, -12,  0, -1, -1,  0, -12,  30],
        [-12, -15, -3, -3, -3, -3, -15, -12],
        [  0,  -3,  0, -1, -1,  0,  -3,   0],
        [ -1,  -3, -1, -1, -1, -1,  -3,  -1],
        [ -1,  -3, -1, -1, -1, -1,  -3,  -1],
        [  0,  -3,  0, -1, -1,  0,  -3,   0],
        [-12, -15, -3, -3, -3, -3, -15, -12],
        [ 30, -12,  0, -1, -1,  0, -12,  30]
        ]

