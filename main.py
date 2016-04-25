#!/usr/bin/env python
import sys

import tdl
import random as rn
import math
import pdb

sys.path.append('/usr/local/lib/python3.4/dist-packages')

CONSOLE_WIDTH = 80
CONSOLE_HEIGHT = 50

MESSAGE_WIDTH = CONSOLE_WIDTH
MESSAGE_HEIGHT = 8

DUNGEON_DISPLAY_WIDTH = 60
DUNGEON_DISPLAY_HEIGHT = CONSOLE_HEIGHT-MESSAGE_HEIGHT

PANEL_WIDTH = CONSOLE_WIDTH - DUNGEON_DISPLAY_WIDTH
PANEL_HEIGHT = CONSOLE_HEIGHT - MESSAGE_HEIGHT

MAP_WIDTH = DUNGEON_DISPLAY_WIDTH
MAP_HEIGHT = DUNGEON_DISPLAY_HEIGHT

MIN_ROOM = 5
MAX_ROOM = 30
MIN_ROOM_SIZE = 5
MAX_ROOM_SIZE = 15

FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 20


light_gray = (150, 150, 150)
white = (255, 255, 255)
light_red = (255, 100, 100)
light_blue = (100, 100, 255)

NOT_VISIBLE_COLORS = {'.': (35, 17, 5), '#': (50, 50, 50)}
VISIBLE_COLORS = {'.': (139, 69, 19), '#': (150, 150, 150)}

MOVEMENT_KEYS = {'KP5': [0, 0], 'KP2': [0, 1], 'KP1': [-1, 1], 'KP4': [-1, 0], 'KP7': [-1, -1], 'KP8': [0, -1], 'KP9': [1, -1], 'KP6': [1, 0], 'KP3': [1, 1]}


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

    def get_center(self):
        return ((int)((self._x1 + self._x2)/2), (int)((self._y1 + self._y2)/2))

    def intersect(self, other_rect):
        return (self._x1 <= other_rect.x2 and self._x2 >= other_rect.x1 and
                self._y1 <= other_rect.y2 and self._y2 >= other_rect.y1)


class Tile:
    def __init__(self, ch, blocked=True, block_sight=True, color=white):
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

    def _get_explored(self):
        return self._explored

    def _set_explored(self, explored):
        self._explored = explored

    explored = property(_get_explored, _set_explored)

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
    def __init__(self, width, height):
        self._width = width
        self._height = height
        self._map_array = [[Tile('#', color=light_gray) for y in range(height)] for x in range(width)]

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

    def is_visible_tile(self, x, y):
        x = int(x)
        y = int(y)

        if x >= MAP_WIDTH or x < 0:
            return False

        elif y >= MAP_HEIGHT or y < 0:
            return False

        elif self._map_array[x][y].blocked:
            return False

        elif self._map_array[x][y].block_sight:
            return False

        else:
            return True

    def is_blocked(self, x, y):
        global entities

        if self.map_array[x][y].blocked:
            return True

        for entity in entities:
            if entity.blocks and entity.x == x and entity.y == y:
                return True

        return False

    # Why don't we define an infinite cost if a monster is there ?
    # Well, if we do so, the aStar alogirhtm basically compute the cost of
    # ALL reachable tiles in the map, without finding a path. So it takes a
    # SHITLOAD amount of time per turn, which is not acceptable. However, if
    # we simply ignore monsters, the current monster WILL go towards the
    # player, and won't be able to move when he encounter one ; still, the path
    # will be computed MUCH faster.
    def move_cost(self, x, y):
        if self.map_array[x][y].blocked:
            return 0
        else:
            return 1

    def place_monsters(self, room):
        global entities

        num_monsters = rn.randint(0, 7)

        for i in range(num_monsters):
            x = rn.randint(room.x1, room.x2 - 1)
            y = rn.randint(room.y1, room.y2 - 1)

            if(rn.random() < 0.8):
                monster = Object(x, y, 'g', name='Genestealer', color=(0, 75, 0), class_name=Fighter(death_function=monster_death), ai=BasicMonster())
            else:
                monster = Object(x, y, 'G', name='Genestealer Alpha', color=(0, 150, 0), class_name=Fighter(death_function=monster_death), ai=BasicMonster())

            entities.append(monster)

    def create_room(self, room):
        for x in range(room.x1, room.x2):
            for y in range(room.y1, room.y2):
                self._map_array[x][y].ch = '.'
                self._map_array[x][y].blocked = False
                self._map_array[x][y].block_sight = False

    def carve_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self._map_array[x][y].ch = '.'
            self._map_array[x][y].blocked = False
            self._map_array[x][y].block_sight = False

    def carve_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self._map_array[x][y].ch = '.'
            self._map_array[x][y].blocked = False
            self._map_array[x][y].block_sight = False

    def create_map(self):
        rooms = []
        num_rooms = 0

        while num_rooms < MAX_ROOM:

            if num_rooms >= MIN_ROOM:
                if rn.random() <= (num_rooms - MIN_ROOM)/(MAX_ROOM - MIN_ROOM):
                    break

            carved = False

            while not carved:

                carved = True

                w = rn.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
                h = rn.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
                x = rn.randint(1, MAP_WIDTH - w - 1)
                y = rn.randint(1, MAP_HEIGHT - h - 1)

                new_room = Rect(x, y, w, h)

                if rooms:
                    for other_room in rooms:
                        if new_room.intersect(other_room):
                            carved = False
                else:
                    carved = True

            self.create_room(new_room)

            (new_x, new_y) = new_room.get_center()

            if num_rooms == 0:
                player.x = new_x
                player.y = new_y

            else:
                closest_room = [-1, -1]
                for i, other_room in enumerate(rooms):
                    if closest_room == [-1, -1]:
                        closest_room = list(other_room.get_center())
                    else:
                        if math.sqrt(pow(other_room.x1 - x, 2) + pow(other_room.y1 - y, 2)) < math.sqrt(pow(closest_room[0] - x, 2) + pow(closest_room[1] - y, 2)):
                            closest_room = list(other_room.get_center())

                if rn.random() > 0.5:
                    self.carve_h_tunnel(x, closest_room[0], y)
                    self.carve_v_tunnel(y, closest_room[1], closest_room[0])
                else:
                    self.carve_v_tunnel(y, closest_room[1], x)
                    self.carve_h_tunnel(x, closest_room[0], closest_room[1])

            self.place_monsters(new_room)
            rooms.append(new_room)
            num_rooms += 1


class Object:
    def __init__(self, x, y, ch, name='DEFAULT_NAME', color=white, blocks=True, class_name=None, ai=None):
        self._x = x
        self._y = y
        self._ch = ch
        self._name = name
        self._color = color
        self._blocks = blocks

        self._class_name = class_name
        if self._class_name:
            self._class_name.owner = self

        self._ai = ai
        if self._ai:
            self._ai.owner = self

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

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name

    name = property(_get_name, _set_name)

    def _get_blocks(self):
        return self._blocks

    def _set_blocks(self, blocks):
        self._blocks = blocks

    blocks = property(_get_blocks, _set_blocks)

    def _get_class_name(self):
        return self._class_name

    def _set_class_name(self, class_name):
        self._class_name = class_name

    class_name = property(_get_class_name, _set_class_name)

    def _get_ai(self):
        return self._ai

    def _set_ai(self, ai):
        self._ai = ai

    ai = property(_get_ai, _set_ai)

    def move(self, delta):
        global game_map

        if not game_map.is_blocked(self._x + delta[0], self._y + delta[1]):
            self._x += delta[0]
            self._y += delta[1]

    def player_move_attack(self, delta):
        global game_map, entities

        new_x = self._x+delta[0]
        new_y = self._y+delta[1]

        target = None

        # We check for entities where we wanna go
        for entity in entities:
            if entity.class_name and entity.x == new_x and entity.y == new_y:
                target = entity

        # If there's one, we attack
        if target is not None:
            if target.class_name is not None:
                player.class_name.attack(target)

        # Else we move
        else:
            self.move(delta)

    # TODO : be sure of that
    def move_towards(self, target_x, target_y):

        dx = target_x - self._x
        dy = target_y - self._y
        distance = math.sqrt(dx**2 + dy**2)
        self.move((dx, dy))

    def distance_to(self, other):
        return round(math.sqrt((other.x - self._x)**2 + (other.y - self._y)**2))

    # Put it at the beginning of the list, so that it'll be overwritted by others on the same tiles
    def send_to_back(self):
        global entities

        entities.remove(self)
        entities.insert(0, self)

    def draw(self, visible_tiles):
        global map_console

        if (self._x, self._y) in visible_tiles:
            map_console.draw_char(self._x, self._y, self._ch, fg=self._color)


class Fighter:
    def __init__(self, hp=10, defense=0, dmg=2, death_function=None):
        self._hp = hp
        self._max_hp = hp
        self._defense = defense
        self._dmg = dmg

        self._death_function = death_function


    def _get_max_hp(self):
        return self._max_hp

    def _set_max_hp(self, max_hp):
        self._max_hp = max_hp

    max_hp = property(_get_max_hp, _set_max_hp)

    def _get_hp(self):
        return self._hp

    def _set_hp(self, hp):
        self._hp = hp

    hp = property(_get_hp, _set_hp)

    def _get_defense(self):
        return self._defense

    def _set_defense(self, defense):
        self._defense = defense

    defense = property(_get_defense, _set_defense)

    def _get_dmg(self):
        return self._dmg

    def _set_dmg(self, dmg):
        self._dmg = dmg

    dmg = property(_get_dmg, _set_dmg)

    def _get_death_function(self):
        return self._death_function

    def _set_death_function(self, death_function):
        self._death_function = death_function

    death_function = property(_get_death_function, _set_death_function)


    def take_damage(self, damage):
        if damage > 0:
            self._hp -= damage

        if self._hp <= 0:
            print('KILLING BLOW ! {} over-damage.'.format(abs(self._hp)))
            function = self.death_function

            if function is not None:
                function(self.owner)


    def attack(self, target):
        damage = self.dmg - target.class_name.defense

        if damage > 0:
            print('{} attacks {} for {} damage.'.format(self.owner.name, target.name, str(damage)))
            target.class_name.take_damage(damage)

        else:
            print('The {} attack doesn\'t scratch the {}'.format(self.owner.name, target.name))


# TODO: last seen player
class BasicMonster:
    global visible_tiles, player, game_map, a_star

    def take_turn(self):
        monster = self.owner

        if (monster.x, monster.y) in visible_tiles:
            if monster.distance_to(player) > 1:
                new_path = a_star.get_path(monster.x, monster.y, player.x, player.y)

                if new_path:
                    monster.move_towards(new_path[0][0], new_path[0][1])

            else:
                monster.class_name.attack(player)


def player_death(player):
    global game_state

    print('You died.')
    game_state = 'dead'

    player.ch = 0x1E
    player.color = (100,0,0)


def monster_death(monster):
    print('The {} died.'.format(monster.name))
    monster.ch = '%'
    monster.color = (100,0,0)
    monster.blocks = False
    monster.class_name = None
    monster.ai = None
    monster.name = 'Remains of ' + monster.name + '.'
    monster.send_to_back()


def handle_keys():
    global fov_recompute, game_state, player

    user_input = tdl.event.key_wait()

    if user_input.type == 'KEYDOWN':
        if user_input.key == 'ESCAPE':
            return 'exit'

    if game_state == 'playing':
        if user_input.type == 'KEYDOWN':
            if user_input.key in MOVEMENT_KEYS:
                player.player_move_attack(MOVEMENT_KEYS[user_input.key])
                fov_recompute = True
        fov_recompute = True

    else:
        return 'didnt_take_turn'


def render_all():
    global fov_recompute, player, game_map, fov_map, visible_tiles
    visible_tiles = []

    if(fov_recompute):
        fov_recompute = False

        # visible_tiles = tdl.map.quickFOV(player.x, player.y, game_map.is_visible_tile(), radius = TORCH_RADIUS, lightWalls = FOV_LIGHT_WALLS)
        visible_tiles_iter = fov_map.compute_fov(player.x, player.y, radius=TORCH_RADIUS, light_walls=FOV_LIGHT_WALLS)

        for tile in visible_tiles_iter:
            visible_tiles.append(tile)

    for x in range(DUNGEON_DISPLAY_WIDTH):
        for y in range(DUNGEON_DISPLAY_HEIGHT):
            if (x, y) in visible_tiles:
                game_map.map_array[x][y].explored = True
                map_console.draw_char(x, y, game_map.map_array[x][y].ch, fg=VISIBLE_COLORS[game_map.map_array[x][y].ch])
            else:
                if game_map.map_array[x][y].explored:
                    map_console.draw_char(x, y, game_map.map_array[x][y].ch, fg=NOT_VISIBLE_COLORS[game_map.map_array[x][y].ch])

    # entities
    for entity in entities:
        entity.draw(visible_tiles)

    # player
    map_console.draw_char(player.x, player.y, player.ch, fg=player.color)

    console.blit(map_console, 0, 0, DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT, 0, 0)

    # render player panel
    for x in range(0, PANEL_WIDTH):
        for y in range(0, PANEL_HEIGHT):
            if x == 0:
                panel.draw_char(x, y, 0xBA, fg=white)
            else:
                panel.draw_char(x, y, 'X', fg=light_red)

    console.blit(panel, DUNGEON_DISPLAY_WIDTH, 0, CONSOLE_WIDTH, CONSOLE_HEIGHT)

    # render message panel
    for x in range(0, MESSAGE_WIDTH):
        for y in range(0, MESSAGE_HEIGHT):
            if y == 0:
                if x == DUNGEON_DISPLAY_WIDTH:
                    message.draw_char(x, y, 0xCA, fg=white)
                else:
                    message.draw_char(x, y, 0xCD, fg=white)

            else:
                message.draw_char(x, y, 'X', fg=light_blue)

    console.blit(message, 0, DUNGEON_DISPLAY_HEIGHT, MESSAGE_WIDTH, MESSAGE_HEIGHT)


# GLOBAL VARIABLES DECLARATIONS
player = Object(x=0, y=0, ch='@', name='Player', class_name=Fighter(hp=30, defense=2, dmg=5))
entities = []
game_map = Map(MAP_WIDTH, MAP_HEIGHT)
fov_map = tdl.map.Map(MAP_WIDTH, MAP_HEIGHT)
visible_tiles = []

fov_recompute = True

a_star = tdl.map.AStar(MAP_WIDTH, MAP_HEIGHT, game_map.move_cost, diagnalCost=0.5)

tdl.set_font('terminal16x16_gs_ro.png')
console = tdl.init(CONSOLE_WIDTH, CONSOLE_HEIGHT)
map_console = tdl.Console(DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT)
panel = tdl.Console(PANEL_WIDTH, PANEL_HEIGHT)
message = tdl.Console(MESSAGE_WIDTH, MESSAGE_HEIGHT)

game_state = 'main_menu'


def main():

    game_map.create_map()

    global fov_map, game_state, entities, player

    for x, y in fov_map:
        fov_map.transparent[x, y] = not game_map.map_array[x][y].block_sight
        fov_map.walkable[x, y] = not game_map.map_array[x][y].blocked

    # Main screen
    for x in range(DUNGEON_DISPLAY_WIDTH):
        for y in range(DUNGEON_DISPLAY_HEIGHT):
            console.draw_char(x, y, ' ')

    console.drawStr(2, 2, "Press any key")
    console.drawStr(2, 3, "to start")

    tdl.flush()

    tdl.event.keyWait()

    game_state = 'playing'

    while not tdl.event.isWindowClosed():
        render_all()

        # Update the window
        tdl.flush()

        player_action = handle_keys()

        if player_action == 'exit':
            break

        elif game_state == 'playing' and player_action != 'didnt_take_turn':
            for entity in entities:
                if entity.ai is not None:
                    entity.ai.take_turn()


if __name__ == '__main__':
    main()
