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

import sys

#Useful for the skill list
from collections import OrderedDict

# Rect
from tools import *


CONSOLE_WIDTH = 90
CONSOLE_HEIGHT = 50

MESSAGE_WIDTH = CONSOLE_WIDTH
MESSAGE_HEIGHT = 12

DUNGEON_DISPLAY_WIDTH = 60
DUNGEON_DISPLAY_HEIGHT = CONSOLE_HEIGHT-MESSAGE_HEIGHT

PANEL_WIDTH = CONSOLE_WIDTH - DUNGEON_DISPLAY_WIDTH
PANEL_HEIGHT = CONSOLE_HEIGHT - MESSAGE_HEIGHT

MAP_WIDTH = 200
MAP_HEIGHT = 200

MIN_ROOM = 5
MAX_ROOM = 30
MIN_ROOM_SIZE = 3
MAX_ROOM_SIZE = 10

GLOBAL_MAX_MONSTER = 40
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

SWARMER_COLORS = ((139,69,19))
SWARMER_ALPHA_COLORS = ((199,129,79))

MAP_TILES = {'wall': '#', 'floor': '.'}
NOT_VISIBLE_COLORS = {'.': (25, 25, 25), '#': (50, 50, 50)}
VISIBLE_COLORS = {'.': (100, 100, 100), '#': (150, 150, 150)}

BAR_WIDTH = PANEL_WIDTH - 8

HP_COLOR = (((75,255,75), (20,80,20)), ((255,100,0), (75,50,0)), ((255,0,0), (150,0,0)))

MESSAGE_COLORS = {'combat':(255,255,150), 'player_combat':(255,255,200)}

MOVEMENT_KEYS = {'5': [0, 0], '2': [0, 1], '1': [-1, 1], '4': [-1, 0], '7': [-1, -1], '8': [0, -1], '9': [1, -1], '6': [1, 0], '3': [1, 1]}

MONSTER_CHANCE = {'Swarmer':95, 'Swarmer Alpha':5}
ITEM_CHANCE = {'Health potion':85, 'Super health potion':5, 'Crowbar':10}

# Name / Base cost, Multiplier, Current level, Tooltip
SKILLS_LIST = OrderedDict([('Meatbag',   [75, 1.5, 0, '(+15HP)']),
                           ('Tough guy', [125, 2, 0, '(+5 HP, +1 armor)']),
                           ('Brawler',   [85, 1.5, 0, '(+5 HP, +1 Melee damage)']),
                           ('Brute',     [100, 1.3, 0, '(+3 Melee damage)']),
                           ('Gunner',    [100, 1.5, 0, '(+2 ranged damage)'])])

MOUSE_COORD = {'x':0, 'y':0}


class Tile:
    def __init__(self, ch, blocked=True, block_sight=True, color=white, bkg_color=None):
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

    def place_monsters(self, room, monster_count):
        global entities

        num_monsters = rn.randint(0, MAX_MONSTERS)

        if not monster_count + num_monsters > GLOBAL_MAX_MONSTER:

            for i in range(num_monsters):
                x = rn.randint(room.x1, room.x2 - 1)
                y = rn.randint(room.y1, room.y2 - 1)

                choice = random_choice(MONSTER_CHANCE)
                if choice == 'Swarmer':
                    monster = create_monster('Swarmer', x, y)
                elif choice == 'Swarmer Alpha':
                    monster = create_monster('Swarmer Alpha', x, y)

                entities.append(monster)

        return monster_count + num_monsters

    def place_items(self, room):
        global entities

        num_items = rn.randint(0,MAX_ITEMS)

        for i in range(num_items):
            x = -1
            y = -1

            while self._map_array[x][y].blocked:
                x = rn.randint(room.x1, room.x2 - 1)
                y = rn.randint(room.y1, room.y2 - 1)

            choice = random_choice(ITEM_CHANCE)

            if choice == 'Health potion':
                item = create_item('Health potion', x, y)
            elif choice == 'Super health potion':
                item = create_item('Super health potion', x, y)
            elif choice == 'Crowbar':
                item = create_item('Crowbar', x, y)

            entities.append(item)
            item.send_to_back()

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

    def reset_map(self):
        global entities

        self._map_array = [[Tile(MAP_TILES['wall'], color=light_gray) for y in range(self._height)] for x in range(self._width)]

        for elem in entities:
            if elem.ai is not None:
                entities.remove(elem)
            elif elem.item is not None:
                entities.remove(item)

    def create_map(self):
        global entities

        rooms = []
        num_rooms = 0

        monster_count = 0

        self.reset_map()
        initialize_fov()

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
            monster_count = self.place_monsters(new_room, monster_count)
            rooms.append(new_room)
            num_rooms += 1

        entities.insert(0, Object(new_x, new_y, '>', 'stairs', blocks=False, always_visible = True))


class Object:
    def __init__(self, x, y, ch, name='DEFAULT_NAME', color=white, bkg_color=None, blocks=True, always_visible = False, class_name=None, ai=None, item=None, equipement=None):
        self._x = x
        self._y = y
        self._ch = ch
        self._name = name
        self._color = color
        self._bkg_color = bkg_color
        self._blocks = blocks
        self._always_visible = always_visible

        self._class_name = class_name
        if self._class_name:
            self._class_name.owner = self

        self._ai = ai
        if self._ai:
            self._ai.owner = self

        self._item = item
        if self._item:
            self._item.owner = self

        self._equipement = equipement
        if self._equipement:
            self._equipement.owner = self
            self._item = Item()
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

    def _get_always_visible(self):
        return self._always_visible

    def _set_always_visible(self, always_visible):
        self._always_visible = always_visible

    always_visible = property(_get_always_visible, _set_always_visible)

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

    def _get_equipement(self):
        return self._equipement

    def _set_equipement(self, equipement):
        self._equipement = equipement

    equipement = property(_get_equipement, _set_equipement)

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

    def draw(self, visible_tiles, boundaries):
        global map_console, game_map

        true_x = self._x - boundaries[0]
        true_y = self._y - boundaries[1]

        if (self._x, self._y) in visible_tiles:
            map_console.draw_char(true_x, true_y, self._ch, fg=self._color, bg=self._bkg_color)
        elif self._always_visible and game_map.map_array[self._x][self._y].explored:
            map_console.draw_char(true_x, true_y, self._ch, fg=self._color, bg=self._bkg_color)

    def force_draw(self):
        global map_console

        map_console.draw_char(self._x, self._y, self._ch, fg=self._color, bg=self._bkg_color)


class BasicClass:
    def __init__(self, hp=10, stamina=10, defense=0, melee_dmg=2, ranged_dmg=1, max_inventory=10, level=1, xp=0, xp_given=0, death_function=None):
        self._hp = hp
        self._max_hp = hp
        self._stamina = stamina
        self._max_stamina = stamina
        self._defense = defense
        self._melee_dmg = melee_dmg
        self._ranged_dmg = ranged_dmg
        self._level = level
        self._xp = xp
        self._xp_given = xp_given

        self._max_inventory = max_inventory
        self._inventory = []

        self._death_function = death_function

    def _get_max_hp(self):
        bonus = sum(equipement.max_hp_bonus for equipement in get_all_equipped(self.owner))
        return self._max_hp + bonus

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
        bonus = sum(equipement.max_stamina_bonus for equipement in get_all_equipped(self.owner))
        return self._max_stamina + bonus

    def _set_max_stamina(self, max_stamina):
        self._max_stamina = max_stamina

    max_stamina = property(_get_max_stamina, _set_max_stamina)

    def _get_defense(self):
        bonus = sum(equipement.defense_bonus for equipement in get_all_equipped(self.owner))
        return self._defense + bonus

    def _set_defense(self, defense):
        self._defense = defense

    defense = property(_get_defense, _set_defense)

    def _get_melee_dmg(self):
        bonus = sum(equipement.melee_dmg_bonus for equipement in get_all_equipped(self.owner))
        return self._melee_dmg + bonus

    def _set_melee_dmg(self, melee_dmg):
        self._melee_dmg = melee_dmg

    melee_dmg = property(_get_melee_dmg, _set_melee_dmg)

    def _get_ranged_dmg(self):
        bonus = sum(equipement.ranged_dmg_bonus for equipement in get_all_equipped(self.owner))
        return self._ranged_dmg + bonus

    def _set_ranged_dmg(self, ranged_dmg):
        self._ranged_dmg = ranged_dmg

    ranged_dmg = property(_get_ranged_dmg, _set_ranged_dmg)

    def _get_level(self):
        return self._level

    def _set_level(self, level):
        self._level = level

    level = property(_get_level, _set_level)

    def _get_xp(self):
        return self._xp

    def _set_xp(self, xp):
        self._xp = xp

    xp = property(_get_xp, _set_xp)

    def add_xp(self, xp):
        self._xp += xp

    def _get_xp_given(self):
        return self._xp_given

    def _set_xp_given(self, xp_given):
        self._xp_given = xp_given

    xp_given = property(_get_xp_given, _set_xp_given)

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

        if self._get_hp() <= 0:
            function = self.death_function

            if function is not None:
                function(self.owner)



    def attack(self, target):
        damage = self._get_melee_dmg() - target.class_name.defense

        msg_color = MESSAGE_COLORS['combat']

        if self.owner.name == 'Player':
            msg_color = MESSAGE_COLORS['player_combat']

        if damage > 0:
            message('{} attacks {} for {} damage.'.format(self.owner.name, target.name, str(damage)), msg_color)
            target.class_name.take_damage(damage)

        else:
            message('The {} attack doesn\'t scratch the {}'.format(self.owner.name, target.name), msg_color)



    def ranged_attack(self, amount):
        target = target_monster()

        if target is not None:
            damage = self._get_ranged_dmg() - target.class_name.defense
        else:
            return False

        msg_color = MESSAGE_COLORS['combat']

        if self.owner.name == 'Player':
            msg_color = MESSAGE_COLORS['player_combat']

            if damage > 0:
                message('{} attacks {} from affar for {} damage.'.format(self.owner.name, target.name, str(damage)), msg_color)
                target.class_name.take_damage(damage)

            else:
                message('The {} ranged attack doesn\'t scratch the {}'.format(self.owner.name, target.name), msg_color)

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
        global entities

        player.class_name.add_to_inventory(self.owner)
        entities.remove(self.owner)
        message('You picked up a {}.'.format(self.owner.name))

    def drop(self):
        global entities

        if self.owner.equippement:
            self.owner.equipement.desequip()

        self.owner.x = player.x
        self.owner.y = player.y

        entities.append(self.owner)
        self.owner.inventory.remove(self.owner)

        message('You dropped a ' + self.owner.name + '.', (0,150,150))


    def use(self):
        if self.owner.equipement:
            self.owner.equipement.toggle_equipped()

        elif self._use_function == None:
            message('The {} can\'t be used.'.format(self.owner.name))

        else:
            if self._use_function(self._function_parameters) != 'cancelled':
                player.class_name.inventory.remove(self.owner)


class Equipement:
    def __init__(self, slot, max_hp_bonus=0, max_stamina_bonus=0, melee_dmg_bonus=0, ranged_dmg_bonus=0, defense_bonus=0):
        self._slot = slot

        self._is_equipped = False

        self._max_hp_bonus = max_hp_bonus
        self._max_stamina_bonus = max_stamina_bonus
        self._melee_dmg_bonus = melee_dmg_bonus
        self._ranged_dmg_bonus = ranged_dmg_bonus
        self._defense_bonus = defense_bonus

    def _get_slot(self):
        return self._slot

    def _set_slot(self, slot):
        self._slot = slot

    slot = property(_get_slot, _set_slot)

    def _get_is_equipped(self):
        return self._is_equipped

    def _set_is_equipped(self, is_equipped):
        self._is_equipped = is_equipped

    is_equipped = property(_get_is_equipped, _set_is_equipped)

    def _get_max_hp_bonus(self):
        return self._max_hp_bonus

    def _set_max_hp_bonus(self, max_hp_bonus):
        self._max_hp_bonus = max_hp_bonus

    max_hp_bonus = property(_get_max_hp_bonus, _set_max_hp_bonus)

    def _get_max_stamina_bonus(self):
        return self._max_stamina_bonus

    def _set_max_stamina_bonus(self, max_stamina_bonus):
        self._max_stamina_bonus = max_stamina_bonus

    max_stamina_bonus = property(_get_max_stamina_bonus, _set_max_stamina_bonus)

    def _get_melee_dmg_bonus(self):
        return self._melee_dmg_bonus

    def _set_melee_dmg_bonus(self, melee_dmg_bonus):
        self._melee_dmg_bonus = melee_dmg_bonus

    melee_dmg_bonus = property(_get_melee_dmg_bonus, _set_melee_dmg_bonus)

    def _get_ranged_dmg_bonus(self):
        return self._ranged_dmg_bonus

    def _set_ranged_dmg_bonus(self, ranged_dmg_bonus):
        self._ranged_dmg_bonus = ranged_dmg_bonus

    ranged_dmg_bonus = property(_get_ranged_dmg_bonus, _set_ranged_dmg_bonus)

    def _get_defense_bonus(self):
        return self._defense_bonus

    def _set_defense_bonus(self, defense_bonus):
        self._defense_bonus = defense_bonus

    defense_bonus = property(_get_defense_bonus, _set_defense_bonus)


    def toggle_equipped(self):
        if self._is_equipped:
            self.desequip()
        else:
            self.equip()

    def equip(self):
        equipped = check_slot(self._slot)
        if equipped:
            equipped.equipement.desequip()

        self._is_equipped = True
        message('Equipped ' + self.owner.name + ' from ' + self._slot + '.', (0,150,150))

    def desequip(self):
        if not self._is_equipped:
            return

        self._is_equipped = False
        message('Desequipped ' + self.owner.name + ' from ' + self._slot + '.', (0,150,150))




def create_monster(monster_name, x, y):
    if monster_name == 'Swarmer':
        return Object(x, y, 's', name='Swarmer', color=(139,69,19), class_name=BasicClass(melee_dmg=rn.randint(1,3), death_function=monster_death, xp_given = 10), ai=BasicMonster())
    elif monster_name == 'Swarmer Alpha':
        return Object(x, y, 'S', name='Swarmer Alpha', color=(199,129,79), class_name=BasicClass(melee_dmg=rn.randint(3,10), death_function=monster_death, xp_given = 100), ai=BasicMonster())


def create_item(item_name, x, y):
    if item_name == 'Health potion':
        return Object(x, y, 0x03, name='Health potion', color=(150, 0, 0), blocks=False, always_visible = True, item=Item(use_function=cast_heal, function_parameters=[3,7]))
    elif item_name == 'Super health potion':
        return Object(x, y, 0x03, name='Super health potion', color=(255, 0, 0), blocks=False, always_visible = True, item=Item(use_function=cast_heal, function_parameters=[50]))
    elif item_name == 'Crowbar':
        return Object(x, y, 0xF4, name='Crowbar', color=(150, 0, 0), blocks=False, always_visible = True, equipement=Equipement(slot='right hand', melee_dmg_bonus=3))





def check_slot(slot):
    global player

    for elem in player.class_name.inventory:
        if elem.equipement and elem.equipement.slot == slot and elem.equipement.is_equipped:
            return elem
    return None

def get_all_equipped(obj):

    if obj == player:
        equipped_list = []

        for item in obj.class_name.inventory:
            if item.equipement and item.equipement.is_equipped:
                equipped_list.append(item.equipement)

        return equipped_list

    else:
        return []





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
                    # Monster
                    else:
                        for entity_2 in entities:
                            if (x,y) != (entity.x,entity.y) and (entity_2.x, entity_2.y) == (x,y) and entity_2.blocks:
                                wall = True

                if not wall:
                    targetable_monsters.append(entity)

    targeted = -1
    current_idx = 0
    max_idx = len(targetable_monsters)

    if len(targetable_monsters) > 0:

        message('Fire mode, choose a target')

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
    global player

    player.class_name.xp += monster.class_name.xp_given

    message('The {} died.'.format(monster.name), (150,0,0))
    monster.ch = '%'
    monster.color = (150, 0, 0)
    monster.blocks = False
    monster.class_name = None
    monster.ai = None
    monster.name = 'Remains of ' + monster.name + '.'
    monster.send_to_back()



def next_level():
    global current_map_level, game_map, entities

    entities.clear()

    message('You go deeper into the complex ...', (150, 0, 150))

    game_map.create_map()
    initialize_fov()

    current_map_level += 1

#CURRENTLY UNUSED
def check_level_up():
    global player

    to_level = 0
    next_level = 100*player.class_name.level

    while player.class_name.xp - next_level >= 0:
        to_level += 1
        next_level = 100*(player.class_name.level)
        player.class_name.xp  -= next_level


    while to_level > 0:

        message('You feel more experimented.')
        player.class_name.level += 1

        tdl.flush()
        render_all()
        tdl.flush()

        choice = None

        while choice == None:
            choice = menu('Level up ! Choose a skill to improve:\n',
                          ['Meatbag (+15HP)',
                           'Tough guy (+5 HP, +1 armor)',
                           'Brawler (+5 HP, +1 Melee damage)',
                           'Brute (+3 Melee damage)',
                           'Gunner (+2 ranged damage)'], MAP_WIDTH)


            if choice == 0:
                player.class_name.max_hp += 15
                player.class_name.hp += 15

            elif choice == 1:
                player.class_name.max_hp += 5
                player.class_name.hp += 5
                player.class_name.defense += 1

            elif choice == 2:
                player.class_name.max_hp += 5
                player.class_name.hp += 5
                player.class_name.melee_dmg += 1

            elif choice == 3:
                player.class_name.melee_dmg += 3

            elif choice == 4:
                player.class_name.ranged_dmg += 2

        to_level -= 1

        tdl.flush()
        render_all()
        tdl.flush()

    tdl.flush()
    render_all()
    tdl.flush()




def random_choice(chances_dict):
    chances = list(chances_dict.values())
    strings = list(chances_dict.keys())

    return strings[random_choice_index(chances)]


def random_choice_index(chances):
    dice = rn.randint(1, sum(chances))

    running_sum = 0
    choice = 0

    for w in chances:
        running_sum += w

        if dice <= running_sum:
            return choice
        choice += 1


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

        if user_input.text == '?':
            help_menu()
            return 'didnt_take_turn'

        if user_input.text == 'c':
            character_stats()
            return 'didnt_take_turn'

        if user_input.text == 'l':
            level_up_screen()
            return 'didnt_take_turn'

        if game_state == 'playing':

            if user_input.text in MOVEMENT_KEYS:
                player.player_move_attack(MOVEMENT_KEYS[user_input.text])

            elif user_input.text is 'g':
                for entity in entities:
                    if entity._item is not None:
                        if player.distance_to(entity) < 2:
                            entity.item.pick_up()
                            break

            elif user_input.text is 'i':
                selected_item = inventory_menu('inventory')
                if selected_item is not None:
                    selected_item.use()
                else:
                    return 'didnt_take_turn'

            elif user_input.text is 'f':
                target = player.class_name.ranged_attack(player.class_name.ranged_dmg)
                if target is None:
                    return 'didnt_take_turn'

            elif user_input.text is '>':
                for elem in entities:
                    if elem.name == 'stairs':
                        if player.x == elem.x and player.y == elem.y:
                            next_level()


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
    height = CONSOLE_HEIGHT - 2 - MESSAGE_HEIGHT
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

    x = 1
    y = 1

    console.blit(menu_console, x, y, width, height, 0, 0)

    tdl.flush()

    user_input = tdl.event.key_wait()

    render_all()
    tdl.flush()

    if user_input.type == 'KEYDOWN':
        if not options:
            return None

        if type(user_input.keychar) is not str or len(user_input.keychar) > 1:
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
        for item in player.class_name.inventory:

            item_name = item.name

            if item.equipement:
                if item.equipement.is_equipped:
                    item_name = '[E] ' + item.name

            options.append(item_name)

        options_colors = [item.color for item in player.class_name.inventory]

    index = menu(header, options, INVENTORY_WIDTH, options_colors=options_colors)

    if index is None:
        return None

    return player.class_name.inventory[index].item


def text_window(header, text, is_file=False):

    width = DUNGEON_DISPLAY_WIDTH-3
    height = DUNGEON_DISPLAY_HEIGHT-3

    text_console = tdl.Console(width, height)
    text_console.set_colors(bg=(0,50,0))
    text_console.draw_rect(1,1,None,None,None,bg=(0,50,0))
    text_console.draw_frame(1,1,None,None,None,bg=(150,250,150))
    text_console.draw_str(int(width/2) - int(len(header)/2) , 1, header, bg=(150,250,150), fg=(0,0,0))

    lines = []

    if is_file:
        for line in text:
            lines.append(textwrap.wrap(line, width-2))

    else:
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



def character_stats():
    global player

    text_window('Character Informations',
                ['Level         : {}'.format(player.class_name.level), '',
                 'XP            : {}'.format(player.class_name.xp), '',
                 'HP            : {}/{}'.format(player.class_name.hp, player.class_name.max_hp), '',
                 'Defense       : {}'.format(player.class_name.defense), '',
                 'Melee damage  : {}'.format(player.class_name.melee_dmg), '',
                 'Ranged damage : {}'.format(player.class_name.ranged_dmg)])

def help_menu():
    text = [line.rstrip('\n') for line in open('help.txt')]
    text_window('Help', text, is_file=True)

def level_up_screen():
    global player

    header = 'Level up screen'

    options = []
    skills_list_helper = []
    skill_cost = []

    for i, skill in enumerate(SKILLS_LIST):
        skills_list_helper.append(skill)
        skill_cost.append(SKILLS_LIST[skill][0] + (SKILLS_LIST[skill][0] * SKILLS_LIST[skill][1] * SKILLS_LIST[skill][2]))

        # Name / Base cost, Multiplier, Current level, Tooltip
        options.append('{} {} level : {} cost to next : {}'.format(skill,
                                                                   SKILLS_LIST[skill][3],
                                                                   SKILLS_LIST[skill][2],
                                                                   skill_cost[i]))

    options_colors = []

    for i, opt in enumerate(options):
        if skill_cost[i] <= player.class_name.xp:
            options_colors.append((255,255,255))
        else:
            options_colors.append((50,50,50))


    choice = menu(header, options, CONSOLE_WIDTH - 2, options_colors)

    tdl.flush()
    render_all()
    tdl.flush()

    if choice is not None:
        if choice > len(SKILLS_LIST):
            return
    else:
        return

    if options_colors[choice] == (255,255,255):
        if choice == 0:
            player.class_name.max_hp += 15
            player.class_name.hp += 15

        elif choice == 1:
            player.class_name.max_hp += 5
            player.class_name.hp += 5
            player.class_name.defense += 1

        elif choice == 2:
            player.class_name.max_hp += 5
            player.class_name.hp += 5
            player.class_name.melee_dmg += 1

        elif choice == 3:
            player.class_name.melee_dmg += 3

        elif choice == 4:
            player.class_name.ranged_dmg += 2

        if SKILLS_LIST[skills_list_helper[choice]][2] == 0:
            message('You learned {}.'.format(skills_list_helper[choice]))
        else:
            message('You improved {}.'.format(skills_list_helper[choice]))

        player.class_name.xp = int(player.class_name.xp - skill_cost[choice])
        SKILLS_LIST[skills_list_helper[choice]][2] += 1


    else:
        message('You don\'t have enough xp for that.')

    tdl.flush()
    render_all()
    tdl.flush()


def move_camera(target_x, target_y):
    x = target_x - DUNGEON_DISPLAY_WIDTH / 2
    y = target_y - DUNGEON_DISPLAY_HEIGHT / 2

    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if x > MAP_WIDTH - DUNGEON_DISPLAY_WIDTH - 1:
        x = MAP_WIDTH - DUNGEON_DISPLAY_WIDTH - 1
    if y > MAP_HEIGHT - DUNGEON_DISPLAY_HEIGHT - 1:
        y = MAP_HEIGHT - DUNGEON_DISPLAY_HEIGHT - 1

    return [int(x), int(y)]

def render_all():
    global fov_recompute, player, game_map, fov_map, visible_tiles, turn_count, current_map_level
    visible_tiles = []

    # for x in range(DUNGEON_DISPLAY_WIDTH):
    #     for y in range(DUNGEON_DISPLAY_HEIGHT):
    #         map_console.draw_char(x, y, ' ')

    map_console.clear()
    boundaries = move_camera(player.x, player.y)

    # visible_tiles = tdl.map.quickFOV(player.x, player.y, game_map.is_visible_tile(), radius = TORCH_RADIUS, lightWalls = FOV_LIGHT_WALLS)
    visible_tiles_iter = fov_map.compute_fov(player.x, player.y, radius=TORCH_RADIUS, light_walls=FOV_LIGHT_WALLS)

    visible_tiles = list(visible_tiles_iter)

    for x in range(DUNGEON_DISPLAY_WIDTH):
        for y in range(DUNGEON_DISPLAY_HEIGHT):

            true_x = x + boundaries[0]
            true_y = y + boundaries[1]

            if (true_x, true_y) in visible_tiles:
                game_map.map_array[true_x][true_y].explored = True
                map_console.draw_char(x, y, game_map.map_array[true_x][true_y].ch, fg=VISIBLE_COLORS[game_map.map_array[true_x][true_y].ch], bg=game_map.map_array[true_x][true_y].bkg_color)
            else:
                if game_map.map_array[true_x][true_y].explored:
                    map_console.draw_char(x, y, game_map.map_array[true_x][true_y].ch, fg=NOT_VISIBLE_COLORS[game_map.map_array[true_x][true_y].ch], bg=game_map.map_array[true_x][true_y].bkg_color)

    # entities
    for entity in entities:
        entity.draw(visible_tiles, boundaries)

    # player
    player.draw(visible_tiles, boundaries)

    console.blit(map_console, 0, 0, DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT, 0, 0)

    # render player panel
    for x in range(PANEL_WIDTH):
        for y in range(PANEL_HEIGHT):
            panel_console.draw_char(x, y, ' ')


    hp_colors = HP_COLOR[0]
    if player.class_name.hp <= player.class_name.max_hp/4:
        hp_colors = HP_COLOR[2]
    elif player.class_name.hp <= player.class_name.max_hp/2:
        hp_colors = HP_COLOR[1]

    panel_console.draw_str(1, 0, 'Level : {}'.format(player.class_name.level))
    panel_console.draw_str(1, 1, 'XP : {}'.format(player.class_name.xp))
    #panel_console.draw_str(1, 1, 'XP : {} (next level : {})'.format(player.class_name.xp, 100*player.class_name.level - player.class_name.xp))

    panel_console.draw_str(1, 3, 'HP', hp_colors[0])
    render_bar(panel_console, 4, 3, BAR_WIDTH, 'HP', player.class_name.hp, player.class_name.max_hp, hp_colors[0], hp_colors[1])

    try:
        render_bar(panel_console, 4, 4, BAR_WIDTH, 'MN', player.class_name.mana, player.class_name.max_mana, (75,75,255), (20,20,80))
        panel_console.draw_str(1, 4, 'MN', fg=(75,75,255))
    except AttributeError:
        render_bar(panel_console, 4, 4, BAR_WIDTH, 'X', BAR_WIDTH, BAR_WIDTH, (75,75,75), (75,75,75))

    try:
        render_bar(panel_console, 4, 5, BAR_WIDTH, 'ST', player.class_name.stamina, player.class_name.max_stamina, (255,255,75), (80,80,20))
        panel_console.draw_str(1, 5, 'ST', fg=(255,255,75))
    except AttributeError:
        render_bar(panel_console, 4, 5, BAR_WIDTH, 'X', BAR_WIDTH, BAR_WIDTH, (75,75,75), (75,75,75))


    panel_console.draw_str(1, PANEL_HEIGHT-1, 'Turn {}'.format(turn_count), fg=(75,75,75))
    panel_console.draw_str(1, PANEL_HEIGHT-2, 'Map level : {}'.format(current_map_level), fg=(150,0,150))


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
    global console, map_console, panel_console, message_console, turn_count

    map_console = tdl.Console(DUNGEON_DISPLAY_WIDTH, DUNGEON_DISPLAY_HEIGHT)

    panel_console = tdl.Console(PANEL_WIDTH, PANEL_HEIGHT)
    message_console = tdl.Console(MESSAGE_WIDTH, MESSAGE_HEIGHT)

    turn_count = 0

def new_game():
    global console, map_console, panel_console, message_console, entities, visible_tiles, player, a_star, game_map, game_state, game_messages, game_messages_history, turn_count, current_map_level

    initialize_consoles()

    entities = []
    visible_tiles = []

    player = Object(x=0, y=0, ch='@', name='Player', class_name=BasicClass(hp=30, defense=2, melee_dmg=5, ranged_dmg=2, death_function=player_death))

    player.class_name.inventory.append(create_item('Crowbar', 0, 0))

    game_map = Map(MAP_WIDTH, MAP_HEIGHT)
    game_map.create_map()

    initialize_fov()

    a_star = tdl.map.AStar(MAP_WIDTH, MAP_HEIGHT, game_map.move_cost, diagnalCost=1)

    game_state = 'main_menu'
    game_messages = []
    game_messages_history = []

    current_map_level = 1

    # Main screen
    for x in range(DUNGEON_DISPLAY_WIDTH):
        for y in range(DUNGEON_DISPLAY_HEIGHT):
            console.draw_char(x, y, ' ')

def initialize_fov():
    global fov_map, fov_recompute, map_console

    fov_recompute = True

    fov_map = tdl.map.Map(MAP_WIDTH, MAP_HEIGHT)

    for x, y in fov_map:
        fov_map.transparent[x, y] = not game_map.map_array[x][y].block_sight
        fov_map.walkable[x, y] = not game_map.map_array[x][y].blocked

    map_console.clear()


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
    global game_map, entities, player, game_messages, game_messages_history, game_state, current_map_level

    file = shelve.open('save', 'n')

    file['game_map'] = game_map
    file['entities'] = entities
    file['player'] = player
    file['game_messages'] = game_messages
    file['game_messages_history'] = game_messages_history
    file['game_state'] = game_state
    file['current_map_level'] = current_map_level

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
    current_map_level = file['current_map_level']

    initialize_consoles()
    initialize_fov()

    return True

def main():
    global console

    tdl.set_font('fonts/Kelora_16x16_diagonal.png')
    console = tdl.init(CONSOLE_WIDTH, CONSOLE_HEIGHT)

    main_menu()

if __name__ == '__main__':
    main()
