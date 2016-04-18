import tdl

CONSOLE_WIDTH = 50
CONSOLE_HEIGHT = 50

class Tile:
	def __init__(self, ch):
		self._ch = ch

	def _get_ch(self):
		return self._ch

	def _set_ch(self, ch):
		self._ch = ch

	ch = property(_get_ch, _set_ch)


class Map:
	def __init__(self,width,height):
		self._width = width
		self._height = height
		self._map_array = [[Tile('#') for x in range(width)] for y in range(height)]

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


def main():

	game_map = Map(50,50)

	tdl.set_font('terminal16x16_gs_ro.png')
	console = tdl.init(CONSOLE_WIDTH,CONSOLE_HEIGHT)

	for x in range(game_map.width):
		for y in range(game_map.height):
			console.draw_char(x, y, game_map.map_array[x][y].ch)

	console.drawStr((int)((CONSOLE_WIDTH/2)-2), (int)(CONSOLE_HEIGHT/2), "Dead")

	tdl.flush()

	tdl.event.keyWait()

	del console


if __name__ == '__main__':
	main()
