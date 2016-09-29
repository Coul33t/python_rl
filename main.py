#!/usr/bin/env python
import sys
sys.path.append('/usr/local/lib/python3.4/dist-packages')

import tdl

import tcod

import random as rn
import math
import textwrap
import shelve
import pdb



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

MAX_MONSTERS = 7
MAX_ITEMS = 1

INVENTORY_WIDTH = DUNGEON_DISPLAY_WIDTH - 2

FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 20


light_gray = (150, 150, 150)
white = (255, 255, 255)
light_red = (255, 100, 100)
light_blue = (100, 100, 255)

MAP_TILES = {'wall': '#', 'floor': '.'}
NOT_VISIBLE_COLORS = {'.': (25, 25, 25), '#': (50, 50, 50)}
VISIBLE_COLORS = {'.': (100, 100, 100), '#': (150, 150, 150)}

BAR_WIDTH = 10

HP_COLOR = (((75,255,75), (20,80,20)), ((255,100,0), (75,50,0)), ((255,0,0), (150,0,0)))

MOVEMENT_KEYS = {'KP5': [0, 0], 'KP2': [0, 1], 'KP1': [-1, 1], 'KP4': [-1, 0], 'KP7': [-1, -1], 'KP8': [0, -1], 'KP9': [1, -1], 'KP6': [1, 0], 'KP3': [1, 1]}


class Rect:
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
    def __init__(self, ch, blocked=True, block_sight=True, color=white, bkg_color = None):
        self._ch = ch
        self._explored = False
        self._blocked = blocked
        self._block_sight = block_sight
        self._color = color
        self._bkg_color = bkg_color

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

    def _get_bkg_color(self):
        return self._bkg_color

    def _set_bkg_color(self, bkg_color):
        self._bkg_color = bkg_color

    bkg_color = property(_get_bkg_color, _set_bkg_color)


class Map:
    def __init__(self, width, height):
        self._width = width
        self._height = height
        self._map_array = [[Tile(MAP_TILES['wall'], color=light_gray) for y in range(height)] for x in range(width)]

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
    # we simply add a high cost for monsters, the current monster WILL go
    # towards the player, and won't be able to move when he encounter another
    # monster ; still, the path will be computed MUCH faster. The cost is
    # set to 10, so that it will still circle around other monsters to get to
    # the player.
    #
    # Basically : if it can't directly reach the player, it will only try 10
    # tiles around itself, instead of the whole map.
    def move_cost(self, x, y):
        if self.map_array[x][y].blocked:
            return 0
        else:
            for entity in entities:
                if entity.blocks and entity.x == x and entity.y == y:
                    return 10

        return 1

    def place_monsters(self, room):
        global entities

        num_monsters = rn.randint(0, MAX_MONSTERS)

        for i in range(num_monsters):
            x = rn.randint(room.x1, room.x2 - 1)
            y = rn.randint(room.y1, room.y2 - 1)

            if(rn.random() < 0.8):
                monster = Object(x, y, 'a', name='Assimilator', color=(139,69,19), class_name=BasicClass(dmg=rn.randint(1,3), death_function=monster_death), ai=BasicMonster())
            else:
                monster = Object(x, y, 'A', name='Assimilator Alpha', color=(199,129,79), class_name=BasicClass(dmg=rn.randint(3,10), death_function=monster_death), ai=BasicMonster())

            entities.append(monster)

    def place_items(self, room):
        global entities

        num_items = rn.randint(0,MAX_ITEMS)

        for i in range(num_items):
            x = -1
            y = -1

            while self._map_array[x][y].blocked:
                x = rn.randint(room.x1, room.x2 - 1)
                y = rn.randint(room.y1, room.y2 - 1)

            if (rn.random() < 0.95):
                current_item = Object(x, y, 0x03, name='Health potion', color=(150, 0, 0), blocks=False, item=Item(use_function=cast_heal, function_parameters=[3,7]))
            else:
                current_item = Object(x, y, 0x03, name='Super health potion', color=(255, 0, 0), blocks=False, item=Item(use_function=cast_heal, function_parameters=[50]))

            entities.append(current_item)
            current_item.send_to_back()

    def create_room(self, room):
        for x in range(room.x1, room.x2):
            for y in range(room.y1, room.y2):
                self._map_array[x][y].ch = MAP_TILES['floor']
                self._map_array[x][y].blocked = False
                self._map_array[x][y].block_sight = False

    def carve_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self._map_array[x][y].ch = MAP_TILES['floor']
            self._map_array[x][y].blocked = False
            self._map_array[x][y].block_sight = False

    def carve_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self._map_array[x][y].ch = MAP_TILES['floor']
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

            self.place_items(new_room)
            self.place_monsters(new_room)
            rooms.append(new_room)
            num_rooms += 1


class Object:
    def __init__(self, x, y, ch, name='DEFAULT_NAME', color=white, bkg_color=None, blocks=True, class_name=None, ai=None, item=None):
        self._x = x
        self._y = y
        self._ch = ch
        self._name = name
        self._color = color
        self._bkg_color = bkg_color
        self._blocks = blocks

        self._class_name = class_name
        if self._class_name:
            self._class_name.owner = self

        self._ai = ai
        if self._ai:
            self._ai.owner = self

        self._item = item
        if self._item:
            self._item.owner = self

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

    def _get_bkg_color(self):
        return self._bkg_color

    def _set_bkg_color(self, bkg_color):
        self._bkg_color = bkg_color

    bkg_color = property(_get_bkg_color, _set_bkg_color)

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

    def _get_item(self):
        return self._item

    def _set_item(self, item):
        self._item = item

    item = property(_get_item, _set_item)

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

    def move_towards(self, target_x, target_y):

        dx = target_x - self._x
        dy = target_y - self._y

        self.move((dx, dy))

    def distance_to(self, other):
        return round(math.sqrt((other.x - self._x)**2 + (other.y - self._y)**2))

    # Put it at the beginning of the list, so that it'll be overwritted by others on the same tiles
    def send_to_back(self):
        global entities

        entities.remove(self)
        entities.insert(0, self)

    def draw(self, visible_tiles):
        global entity_console

        if (self._x, self._y) in visible_tiles:
            entity_console.draw_char(self._x, self._y, self._ch, fg=self._color, bg=self._bkg_color)

    def force_draw(self):
        global entity_console

        entity_console.draw_char(self._x, self._y, self._ch, fg=self._color, bg=self._bkg_color)


class BasicClass:
    def __init__(self, hp=10, stamina=10, defense=0, dmg=2, max_inventory=10, death_function=None):
        self._hp = hp
        self._max_hp = hp
        self._stamina = stamina
        self._max_stamina = stamina
        self._defense = defense
        self._dmg = dmg

        self._max_inventory = max_inventory
        self._inventory = []

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

    def _get_stamina(self):
        return self._stamina

    def _set_stamina(self, stamina):
        self._stamina = stamina

    stamina = property(_get_stamina, _set_stamina)

    def _get_max_stamina(self):
        return self._max_stamina

    def _set_max_stamina(self, max_stamina):
        self._max_stamina = max_stamina

    max_stamina = property(_get_max_stamina, _set_max_stamina)

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

    def _get_max_inventory(self):
        return self._max_inventory

    def _set_max_inventory(self, max_inventory):
        self._max_inventory = max_inventory

    max_inventory = property(_get_max_inventory, _set_max_inventory)

    def _get_inventory(self):
        return self._inventory

    def _set_inventory(self, inventory):
        self._inventory = inventory

    inventory = property(_get_inventory, _set_inventory)

    def add_to_inventory(self, item_to_add):
        self._inventory.append(item_to_add)

    def _get_death_function(self):
        return self._death_function

    def _set_death_function(self, death_function):
        self._death_function = death_function

    death_function = property(_get_death_function, _set_death_function)



    def take_damage(self, damage):
        if damage > 0:
            self._hp -= damage

        if self._hp <= 0:
            function = self.death_function

            if function is not None:
                function(self.owner)



    def attack(self, target):
        damage = self.dmg - target.class_name.defense

        color_dmg = (255,255,255)
        color_no_dmg = (255,255,255)

        if self.owner.name == 'Player':
            color_dmg = (255,255,255)
            color_no_dmg = (255,255,255)

        if damage > 0:
            message('{} attacks {} for {} damage.'.format(self.owner.name, target.name, str(damage)), color_dmg)
            target.class_name.take_damage(damage)

        else:
            message('The {} attack doesn\'t scratch the {}'.format(self.owner.name, target.name), color_no_dmg)



    def ranged_attack(self, amount):
        target = target_monster()
        
        if target is not None:
            damage = self.dmg - target.class_name.defense

            color_dmg = (255,255,255)
            color_no_dmg = (255,255,255)

            if self.owner.name == 'Player':
                color_dmg = (255,255,255)
                color_no_dmg = (255,255,255)

            if damage > 0:
                message('{} attacks {} from affar for {} damage.'.format(self.owner.name, target.name, str(damage)), color_dmg)
                target.class_name.take_damage(damage)

            else:
                message('The {} ranged attack doesn\'t scratch the {}'.format(self.owner.name, target.name), color_no_dmg)

        return target



    def heal(self, amount):
        before_heal = self._hp
        self._hp += amount
        if self._hp > self._max_hp:
            self._hp = self._max_hp
        message('You drink a potion. You regain {} HP (effective : +{}).'.format(amount, self._hp - before_heal))


class BasicMonster:
    global visible_tiles, player, game_map, a_star

    def __init__(self):
        self._last_seen_player = (None, None)

    def take_turn(self):
        monster = self.owner

        if (monster.x, monster.y) in visible_tiles:
            if monster.distance_to(player) > 1:
                new_path = a_star.get_path(monster.x, monster.y, player.x, player.y)
                self._last_seen_player = ( player.x, player.y)

                if new_path:
                    monster.move_towards(new_path[0][0], new_path[0][1])

            else:
                monster.class_name.attack(player)


        elif not self._last_seen_player == (None, None):
            new_path = a_star.get_path(monster.x, monster.y, self._last_seen_player[0], self._last_seen_player[1])

            if new_path:
                monster.move_towards(new_path[0][0], new_path[0][1])


class Item:
    def __init__(self, use_function=None, function_parameters=None):
        self._use_function = use_function
        self._function_parameters = function_parameters


    def _get_use_function(self):
        return self._use_function

    def _set_use_function(self, use_function):
        self._use_function = use_function

    use_function = property(_get_use_function, _set_use_function)

    def pick_up(self):
        player.class_name.add_to_inventory(self.owner)
        entities.remove(self.owner)
        message('You picked up a {}.'.format(self.owner.name))

    def use(self):
        if self._use_function == None:
            message('The {} can\'t be used.'.format(self.owner.name))
        else:
            if self._use_function(self._function_parameters) != 'cancelled':
                player.class_name.inventory.remove(self.owner)





def cast_heal(amount):
    if type(amount) is list:
        if len(amount) == 1:
            amount = amount[0]
        elif len(amount) == 2:
            amount = rn.randint(amount[0], amount[1])
        player.class_name.heal(amount)

    else:
        raise TypeError('The amount is not a list.')





def target_monster():
    global visible_tiles, entities, map_console, game_map

    targetable_monsters = []
    untargetable_wall = 0
    untargetable_monster = 0

    # Here, we check for every monsters available to targeting.
    # 1) draw a bresenham line between the player and the entity
    # 2a) if there's a wall in the path, do not allow targeting
    # 2b) if there's a monster in the path, do not allow targeting
    # 3) else, put the monster in the targetable list
    for entity in entities:
        # If it's a monster, basically
        if entity.ai is not None:
            if (entity.x, entity.y) in visible_tiles:
                
                wall = False
                
                path_to_monster = tdl.map.bresenham(player.x, player.y, entity.x, entity.y)
                
                # If the path is blocked by a wall or a monster, we don't allow the player to shoot at it
                for x,y in path_to_monster:
                    # Wall
                    if game_map.map_array[x][y].blocked:
                        wall = True
                        untargetable_wall += 1
                    # Monster
                    else:
                        for entity_2 in entities:
                            if (x,y) != (entity.x,entity.y) and (entity_2.x, entity_2.y) == (x,y) and entity_2.blocks:
                                wall = True
                                untargetable_monster += 1
                
                if not wall:
                    targetable_monsters.append(entity)

    targeted = -1
    current_idx = 0
    max_idx = len(targetable_monsters)

    if len(targetable_monsters) > 0:

        message('Fire mode, choose a target ({} blocked by wall, {} blocked by monsters)'.format(untargetable_wall, untargetable_monster))

        path_to_monster = tdl.map.bresenham(player.x, player.y, targetable_monsters[0].x, targetable_monsters[0].y)

        while targeted is not None:
            if current_idx == max_idx:
                current_idx = 0

            targeted = targetable_monsters[current_idx]

            if current_idx == 0:
                last_entity = targetable_monsters[-1]
            else:
                last_entity = targetable_monsters[current_idx - 1]

            last_path = path_to_monster
            path_to_monster = tdl.map.bresenham(player.x, player.y, targetable_monsters[current_idx].x, targetable_monsters[current_idx].y)


            for x,y in last_path:
                game_map.map_array[x][y].bkg_color = Ellipsis

            for x,y in path_to_monster:
                game_map.map_array[x][y].bkg_color = (150,150,150)

            

            last_entity.bkg_color = Ellipsis
            last_entity.force_draw()
     
            targetable_monsters[current_idx].bkg_color = white
            targetable_monsters[current_idx].force_draw()
            
            render_all()
            tdl.flush()
            

            user_input = None

            for event in tdl.event.get():
                if event.type == 'KEYDOWN':
                    user_input = event

            if user_input:
                if user_input.type == 'KEYDOWN':
                    if user_input.key == 'SPACE':
                        targeted = targetable_monsters[current_idx]
                        break

                    elif user_input.key == 'TAB':
                        current_idx += 1

                    elif user_input.keychar == 'c':
                        targeted = None

        targetable_monsters[current_idx].bkg_color = Ellipsis
        targetable_monsters[current_idx].force_draw()

        for x,y in path_to_monster:
            game_map.map_array[x][y].bkg_color = Ellipsis

        for x,y in last_path:
            game_map.map_array[x][y].bkg_color = Ellipsis

        render_all()
        tdl.flush()

        return targeted

    render_all()
    tdl.flush()

    return None





def player_death(player):
    global game_state

    message('You died.', (150,0,0))
    game_state = 'dead'

    player.ch = 0x1E
    player.color = (200, 0, 0)


def monster_death(monster):
    message('The {} died.'.format(monster.name), (150,0,0))
    monster.ch = '%'
    monster.color = (150, 0, 0)
    monster.blocks = False
    monster.class_name = None
    monster.ai = None
    monster.name = 'Remains of ' + monster.name + '.'
    monster.send_to_back()





def handle_keys():
    global fov_recompute, game_state, player

    user_input = None

    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event

    if user_input:
        if user_input.key == 'ESCAPE':

            if game_state == 'playing':
                save_game()

            return 'exit'

        if user_input.keychar == '?':
            help_menu()
            return 'didnt_take_turn'

        if game_state == 'playing':

            if user_input.key in MOVEMENT_KEYS:
                player.player_move_attack(MOVEMENT_KEYS[user_input.key])

            elif user_input.keychar is 'g':
                for entity in entities:
                    if entity._item is not None:
                        if player.distance_to(entity) < 2:
                            entity.item.pick_up()
                            break

            elif user_input.keychar is 'i':
                selected_item = inventory_menu('inventory')
                if selected_item is not None:
                    selected_item.use()
                else:
                    return 'didnt_take_turn'

            elif user_input.keychar is 'f':
                target = player.class_name.ranged_attack(player.class_name.dmg)
                if target is None:
                    return 'didnt_take_turn'

            else:
                return 'didnt_take_turn'




    else:
        return 'didnt_take_turn'


def render_bar(target_console, x, y, total_width, name, value, maximum, bar_color, empty_color):
    bar_width = math.ceil(float(value) / maximum * total_width)

    if name is not 'X':
        target_console.draw_rect(x, y, total_width, 1, 0xB0, fg = empty_color)


        if bar_width > 0:
            target_console.draw_rect(x, y, bar_width, 1, 0xB0, fg = bar_color)


        target_console.draw_str(PANEL_WIDTH - 3, y, str(value), fg = bar_color)


def message(new_msg, color=(255, 255, 255)):
    new_msg_lines = textwrap.wrap(new_msg, MESSAGE_WIDTH)

    for line in new_msg_lines:
        if len(game_messages) == MESSAGE_HEIGHT - 1:
            del game_messages[0]

        game_messages.append((line, color))

    game_messages_history.append(new_msg)


def menu(header, options, width, options_colors=None):
    height = 15
    menu_console = tdl.Console(width, height)
    menu_console.set_colors(bg=(10,10,50))
    menu_console.draw_rect(0,0,None,None,None, bg=(10,10,50))
    menu_console.draw_frame(0,0,None,None,None, bg=(25,25,150))
    menu_console.draw_str(int(width/2) - int(len(header)/2) , 0, header)

    y = 1
    x = 1

    letter = ord('a')

    for idx, option_text in enumerate(options):
        text = '({}) {}'.format(chr(letter+idx), option_text)
        if(options_colors):
            menu_console.draw_str(x, y, text, fg=options_colors[idx])
        else:
            menu_console.draw_str(x, y, text)
        y += 1

    x = int(DUNGEON_DISPLAY_WIDTH/2) - int(width/2)
    y = int(DUNGEON_DISPLAY_HEIGHT/2) - int(height/2)

    console.blit(menu_console, x, y, width, height, 0, 0)

    tdl.flush()

    user_input = tdl.event.key_wait()

    render_all()
    tdl.flush()

    if user_input.type == 'KEYDOWN':
        if not options:
            return None

        index = ord(user_input.keychar) - ord('a')

        # Because if the inventory is empty, there's still a (a) option
        if index >= 0 and index < len(options):
            return index
        return None



def inventory_menu(header):
    options = []
    options_colors = []

    if player.class_name.inventory:
        options = [item.name for item in player.class_name.inventory]
        options_colors = [item.color for item in player.class_name.inventory]

    index = menu(header, options, INVENTORY_WIDTH, options_colors=options_colors)

    if index is None:
        return None

    return player.class_name.inventory[index].item


def text_window(header, text):

    width = DUNGEON_DISPLAY_WIDTH-3
    height = DUNGEON_DISPLAY_HEIGHT-3

    text_console = tdl.Console(width, height)
    text_console.set_colors(bg=(0,50,0))
    text_console.draw_rect(1,1,None,None,None,bg=(0,50,0))
    text_console.draw_frame(1,1,None,None,None,bg=(150,250,150))
    text_console.draw_str(int(width/2) - int(len(header)/2) , 1, header, bg=(150,250,150), fg=(0,0,0))

    lines = []

    for line in text:
        lines.append(textwrap.wrap(line, width-2))

    y = 2
    for line_to_print in lines:
        text_console.draw_str(int(2), int(y), str(*line_to_print))
        y += 1

    console.blit(text_console, 1, 1, width, height, 0, 0)

    tdl.flush()
    user_input = tdl.event.key_wait()

    render_all()
    tdl.flush()
    if user_input.type == 'KEYDOWN':
        return None



def help_menu():
    text = [line.rstrip('\n') for line in open('help.txt')]
    text_window('Help', text)


def render_all():
    global fov_recompute, player, game_map, fov_map, visible_tiles, turn_count
    visible_tiles = []


    # visible_tiles = tdl.map.quickFOV(player.x, player.y, game_map.is_visible_tile(), radius = TORCH_RADIUS, lightWalls = FOV_LIGHT_WALLS)
    visible_tiles_iter = fov_map.compute_fov(player.x, player.y, radius=TORCH_RADIUS, light_walls=FOV_LIGHT_WALLS)

    for tile in visible_tiles_iter:
        visible_tiles.append(tile)

    for x in range(DUNGEON_DISPLAY_WIDTH):
        for y in range(DUNGEON_DISPLAY_HEIGHT):
            if (x, y) in visible_tiles:
                game_map.map_array[x][y].explored = True
                map_console.draw_char(x, y, game_map.map_array[x][y].ch, fg=VISIBLE_COLORS[game_map.map_array[x][y].ch], bg=game_map.map_array[x][y].bkg_color)
            else:
                if game_map.map_array[x][y].explored:
                    map_console.draw_char(x, y, game_map.map_array[x][y].ch, fg=NOT_VISIBLE_COLORS[game_map.map_array[x][y].ch], bg=game_map.map_array[x][y].bkg_color)

    entity_console.clear()
    # entities
    for entity in entities:
        entity.draw(visible_tiles)

    # player
    entity_console.draw_char(player.x, player.y, player.ch, fg=player.color, bg=player.bkg_color)

    console.blit(map_console, 0, 0, DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT, 0, 0)

    console.blit(entity_console, 0, 0, DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT, 0, 0, bgalpha=0.0)

    # render player panel
    for x in range(MESSAGE_WIDTH):
        for y in range(3):
            panel_console.draw_char(x, y, ' ')


    hp_colors = HP_COLOR[0]
    if player.class_name.hp <= player.class_name.max_hp/4:
        hp_colors = HP_COLOR[2]
    elif player.class_name.hp <= player.class_name.max_hp/2:
        hp_colors = HP_COLOR[1]


    panel_console.draw_str(1, 0, ' ')
    panel_console.draw_str(1, 0, 'HP', hp_colors[0])
    render_bar(panel_console, 4, 0, BAR_WIDTH, 'HP', player.class_name.hp, player.class_name.max_hp, hp_colors[0], hp_colors[1])

    try:
        render_bar(panel_console, 4, 1, BAR_WIDTH, 'MN', player.class_name.mana, player.class_name.max_mana, (75,75,255), (20,20,80))
        panel_console.draw_str(1, 1, 'MN', fg=(75,75,255))
    except AttributeError:
        render_bar(panel_console, 4, 1, BAR_WIDTH, 'X', BAR_WIDTH, BAR_WIDTH, (75,75,75), (75,75,75))

    try:
        render_bar(panel_console, 4, 2, BAR_WIDTH, 'ST', player.class_name.stamina, player.class_name.max_stamina, (255,255,75), (80,80,20))
        panel_console.draw_str(1, 2, 'ST', fg=(255,255,75))
    except AttributeError:
        render_bar(panel_console, 4, 2, BAR_WIDTH, 'X', BAR_WIDTH, BAR_WIDTH, (75,75,75), (75,75,75))

    panel_console.draw_str(1, PANEL_HEIGHT-2, str(turn_count), fg=(75,75,75))

    for x in range(0, PANEL_WIDTH):
        for y in range(0, PANEL_HEIGHT):
            if x == 0:
                panel_console.draw_char(x, y, 0xBA, fg=white)

    console.blit(panel_console, DUNGEON_DISPLAY_WIDTH, 0, CONSOLE_WIDTH, CONSOLE_HEIGHT)

    # render message panel
    for x in range(0, MESSAGE_WIDTH):
        for y in range(0, MESSAGE_HEIGHT):
            if y == 0:
                if x == DUNGEON_DISPLAY_WIDTH:
                    message_console.draw_char(x, y, 0xCA, fg=white)
                else:
                    message_console.draw_char(x, y, 0xCD, fg=white)

            else:
                message_console.draw_char(x, y, ' ')

    y = 1
    for (line, color) in game_messages:
        message_console.draw_str(0, y, line, fg=color)
        y += 1

    console.blit(message_console, 0, DUNGEON_DISPLAY_HEIGHT, MESSAGE_WIDTH, MESSAGE_HEIGHT)


# GLOBAL VARIABLES DECLARATIONS



def main_menu():
    global console

    console.draw_str(2, 2, "Welcome to [NAME ERROR]")
    console.draw_str(2, 4, "(1) New Game")
    console.draw_str(2, 5, "(2) Load Game")
    console.draw_str(2, 6, "(3) Quit")

    tdl.flush()

    key = tdl.event.key_wait()

    if key.keychar == '1' or key.keychar == 'KP1':
        new_game()
        play_game()


    elif key.keychar == '2' or key.keychar == 'KP2':
        
        try:
            load_game()

        except:
            for x in range(DUNGEON_DISPLAY_WIDTH):
                for y in range(DUNGEON_DISPLAY_HEIGHT):
                    console.draw_char(x, y, ' ')

            console.draw_str(2,5, "No savegame ! Launching new game, press any key to continue")
            tdl.flush()
            key = tdl.event.key_wait()
            
            new_game()
        
        play_game()


    elif key.keychar =='3' or key.keychar == 'KP3':
        pass



def initialize_consoles():
    global console, map_console, panel_console, message_console, entity_console, turn_count

    map_console = tdl.Console(DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT)

    entity_console = tdl.Console(DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT)

    panel_console = tdl.Console(PANEL_WIDTH, PANEL_HEIGHT)
    message_console = tdl.Console(MESSAGE_WIDTH, MESSAGE_HEIGHT)

    turn_count = 0

def new_game():
    global console, map_console, panel_console, message_console, entities, visible_tiles, player, a_star, game_map, game_state, game_messages, game_messages_history, turn_count

    initialize_consoles()

    entities = []
    visible_tiles = []

    player = Object(x=0, y=0, ch='@', name='Player', class_name=BasicClass(hp=30, defense=2, dmg=5, death_function=player_death))

    game_map = Map(MAP_WIDTH, MAP_HEIGHT)
    game_map.create_map()

    initialize_fov()

    a_star = tdl.map.AStar(MAP_WIDTH, MAP_HEIGHT, game_map.move_cost, diagnalCost=1)

    game_state = 'main_menu'
    game_messages = []
    game_messages_history = []
  

    # Main screen
    for x in range(DUNGEON_DISPLAY_WIDTH):
        for y in range(DUNGEON_DISPLAY_HEIGHT):
            console.draw_char(x, y, ' ')

def initialize_fov():
    global fov_map, fov_recompute

    fov_recompute = True

    fov_map = tdl.map.Map(MAP_WIDTH, MAP_HEIGHT)

    for x, y in fov_map:
        fov_map.transparent[x, y] = not game_map.map_array[x][y].block_sight
        fov_map.walkable[x, y] = not game_map.map_array[x][y].blocked

def play_game():

    global game_state, entities, turn_count

    game_state = 'playing'

    render_all()
    tdl.flush()

    while not tdl.event.isWindowClosed():
        player_action = 'didnt_take_turn'

        while player_action == 'didnt_take_turn':
            player_action = handle_keys()

        if player_action == 'exit':
            break

        elif game_state == 'playing' and player_action != 'didnt_take_turn':
            for entity in entities:
                if entity.ai is not None:
                    entity.ai.take_turn()


        turn_count += 1

        render_all()

        # Update the window
        
        tdl.flush()
        
def save_game():
    global game_map, entities, player, game_messages, game_messages_history, game_state

    file = shelve.open('save', 'n')

    file['game_map'] = game_map
    file['entities'] = entities
    file['player'] = player
    file['game_messages'] = game_messages
    file['game_messages_history'] = game_messages_history
    file['game_state'] = game_state

    file.close()

def load_game():
    global game_map, entities, player, game_messages, game_messages_history, game_state

    file = shelve.open('save', 'n')

    game_map = file['game_map']
    entities = file['entities']
    player = file['player']
    game_messages = file['game_messages'] 
    game_messages_history = file['game_messages_history']
    game_state = file['game_state']

    initialize_consoles()
    initialize_fov()

def main():
    global console

    tdl.set_font('SFE_Curses_square_16x16.png')
    console = tdl.init(CONSOLE_WIDTH, CONSOLE_HEIGHT)

    main_menu()

if __name__ == '__main__':
    main()
