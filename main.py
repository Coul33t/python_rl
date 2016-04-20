#!/usr/bin/env python
import sys
sys.path.append('/usr/local/lib/python3.4/dist-packages') 

import tdl
import pdb

CONSOLE_WIDTH = 80
CONSOLE_HEIGHT = 50

MESSAGE_WIDTH = CONSOLE_WIDTH
MESSAGE_HEIGHT = 8

DUNGEON_DISPLAY_WIDTH = 60
DUNGEON_DISPLAY_HEIGHT = CONSOLE_HEIGHT-MESSAGE_HEIGHT

PANEL_WIDTH = CONSOLE_WIDTH - DUNGEON_DISPLAY_WIDTH
PANEL_HEIGHT = CONSOLE_HEIGHT - MESSAGE_HEIGHT

MAP_WIDTH = 200
MAP_HEIGHT = 200

light_gray = (150,150,150)
white = (255,255,255)
light_red = (255,100,100)
light_blue = (100,100,255)

MOVEMENT_KEYS = {'KP5': [0,0], 'KP2': [0,1], 'KP1': [-1,1], 'KP4': [-1,0], 'KP7': [-1,-1], 'KP8': [0,-1], 'KP9': [1,-1], 'KP6': [1,0], 'KP3': [1,1]}
GAME_STATE = 'main_menu'




class Rect():
	def __init__(self, x, y, w, h):
		self._x1 = x
		self._y1 = y
		self._x2 = x + w
		self._y2 = y + h

	def _get_x1(self):
		return self._x1

	def _set_x1(self, x1):
		self._x1 = x1

	x1 = property(_get_x1, _set_x1)

	
	def _get_y1(self):
		return self._y1

	def _set_y1(self, y1):
		self._y1 = y1

	y1 = property(_get_y1, _set_y1)

	
	def _get_x2(self):
		return self._x2

	def _set_x2(self, x2):
		self._x2 = x2

	x2 = property(_get_x2, _set_x2)

	
	def _get_y2(self):
		return self._y2

	def _set_y2(self, y2):
		self._y2 = y2

	y2 = property(_get_y2, _set_y2)







class Tile:
	def __init__(self, ch, blocked = True, block_sight = True, color = white):
		self._ch = ch
		self._explored = False
		self._blocked = blocked
		self._block_sight = block_sight
		self._color = color


	def _get_ch(self):
		return self._ch

	def _set_ch(self, ch):
		self._ch = ch

	ch = property(_get_ch, _set_ch)

	
	def _get_blocked(self):
		return self._blocked

	def _set_blocked(self, blocked):
		self._blocked = blocked

	blocked = property(_get_blocked, _set_blocked)


	def _get_block_sight(self):
		return self._block_sight

	def _set_block_sight(self, block_sight):
		self._block_sight = block_sight

	block_sight = property(_get_block_sight, _set_block_sight)


	def _get_color(self):
		return self._color

	def _set_color(self, color):
		self._color = color

	color = property(_get_color, _set_color)





class Map:
	def __init__(self,width,height):
		self._width = width
		self._height = height
		self._map_array = [[Tile('#', color = light_gray) for x in range(width)] for y in range(height)]

	def _get_width(self):
		return self._width

	def _set_width(self, width):
		self._width = width

	width = property(_get_width, _set_width)

	def _get_height(self):
		return self._height

	def _set_height(self, height):
		self._height = height

	height = property(_get_height, _set_height)

	def _get_map_array(self):
		return self._map_array

	def _set_map_array(self, map_array):
		self._map_array = map_array

	map_array = property(_get_map_array, _set_map_array)

	
	def create_room(self, room):
		for x in range(room.x1 + 1, room.x2):
			for y in range(room.y1 + 1, room.y2):
				self._map_array[x][y].blocked = False
				self._map_array[x][y].block_sight = False

	def carve_h_tunnel(self, x1, x2, y):
		for x in range(x1, x2):
			self._map_array[x][y].blocked = False
			self._map_array[x][y].block_sight = False

	def carve_v_tunnel(self, y1, y2, x):
		for y in range(y1, y2):
			self._map_array[x][y].blocked = False
			self._map_array[x][y].block_sight = False

	def create_map(self):
		room1 = Rect(2,2,10,10)
		room2 = Rect(14,14,20,20)
		self.create_room(room1)
		self.create_room(room2)
		self.carve_h_tunnel(6, 23, 6)
		self.carve_v_tunnel(6, 17, 23)





class Object():
	def __init__(self, x, y, ch, color=white):
		self._x = x
		self._y = y
		self._ch = ch
		self._color = color


	def _get_x(self):
		return self._x

	def _set_x(self, x):
		self._x = x

	x = property(_get_x, _set_x)


	def _get_y(self):
		return self._y

	def _set_y(self, y):
		self._y = y

	y = property(_get_y, _set_y)


	def _get_ch(self):
		return self._ch

	def _set_ch(self, ch):
		self._ch = ch

	ch = property(_get_ch, _set_ch)


	def _get_color(self):
		return self._color

	def _set_color(self, color):
		self._color = color

	color = property(_get_color, _set_color)






class Hero(Object):
	def __init__(self, x, y, color=white):
		Object.__init__(self, x, y, '@', color)

	def move(self, delta):
		if not game_map.map_array[self._x+delta[0]][self._y+delta[1]].blocked:
			self._x += delta[0]
			self._y += delta[1]
	




def handle_keys(player):
	user_input = tdl.event.key_wait()

	if user_input.type == 'KEYDOWN':
		if user_input.key == 'ESCAPE':
			return 'exit'

	if GAME_STATE == 'playing':
		if user_input.type == 'KEYDOWN':
			if user_input.key in MOVEMENT_KEYS:
				player.move(MOVEMENT_KEYS[user_input.key])




def render_all(player):
	#render map
	#tiles
	for x in range(DUNGEON_DISPLAY_WIDTH):
		for y in range(DUNGEON_DISPLAY_HEIGHT):
			if not game_map.map_array[x][y].blocked:
				map_console.draw_char(x, y, '.', fg = game_map.map_array[x][y].color)
			else:
				map_console.draw_char(x, y, '#', fg = game_map.map_array[x][y].color)


	#entities
	for entity in entities:
		map_console.draw_char(entity.x, entity.y, entity.ch, fg = entity.color)

	#player
	map_console.draw_char(player.x, player.y, player.ch, fg = player.color)

	console.blit(map_console, 0, 0, DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT, 0, 0)
	
	#render player panel
	for x in range(0, PANEL_WIDTH):
		for y in range(0, PANEL_HEIGHT):
			if x == 0:
				panel.draw_char(x, y, 0xBA, fg = white)
			else:
				panel.draw_char(x, y, 'X', fg = light_red)

	console.blit(panel, DUNGEON_DISPLAY_WIDTH, 0, CONSOLE_WIDTH, CONSOLE_HEIGHT)

	#render message panel
	for x in range(0, MESSAGE_WIDTH):
		for y in range(0, MESSAGE_HEIGHT):
			if y == 0:
				if x == DUNGEON_DISPLAY_WIDTH:
					message.draw_char(x, y, 0xCA, fg = white)
				else:
					message.draw_char(x, y, 0xCD, fg = white) 
				
			else:
				message.draw_char(x, y, 'X', fg = light_blue)

	console.blit(message, 0, DUNGEON_DISPLAY_HEIGHT, MESSAGE_WIDTH, MESSAGE_HEIGHT)





# GLOBAL VARIABLES DECLARATIONS
entities = []
game_map = Map(MAP_WIDTH,MAP_HEIGHT)

tdl.set_font('terminal16x16_gs_ro.png')
console = tdl.init(CONSOLE_WIDTH,CONSOLE_HEIGHT)
map_console = tdl.Console(DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT)
panel = tdl.Console(PANEL_WIDTH, PANEL_HEIGHT)
message = tdl.Console(MESSAGE_WIDTH, MESSAGE_HEIGHT)

def main():

	player = Hero(10, 10)
	game_map.create_map()

	# Main screen
	for x in range(DUNGEON_DISPLAY_WIDTH):
		for y in range(DUNGEON_DISPLAY_HEIGHT):
			console.draw_char(x, y, ' ')

	console.drawStr(2, 2, "Press any key")
	console.drawStr(2, 3, "to start")


	tdl.flush()

	tdl.event.keyWait()

	global GAME_STATE 
	GAME_STATE = 'playing'

	while not tdl.event.isWindowClosed():
		render_all(player)

		# Update the window
		tdl.flush()

		player_action = handle_keys(player)

		if player_action == 'exit':
			break


if __name__ == '__main__':
	main()
