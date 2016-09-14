import constants as cst
import random as rn
import components as comp

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
    def __init__(self, ch, blocked=True, block_sight=True, color=cst.white):
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
        self._map_array = [[Tile('#', color=cst.light_gray) for y in range(height)] for x in range(width)]

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

        num_monsters = rn.randint(0, cst.MAX_MONSTERS)

        for i in range(num_monsters):
            x = rn.randint(room.x1, room.x2 - 1)
            y = rn.randint(room.y1, room.y2 - 1)

            if(rn.random() < 0.8):
                monster = Object(x, y, 'g', name='Genestealer', color=(0, 75, 0), class_name=comp.BasicClass(dmg=rn.randint(1,3), death_function=monster_death), ai=BasicMonster())
            else:
                monster = Object(x, y, 'G', name='Genestealer Alpha', color=(0, 150, 0), class_name=comp.BasicClass(dmg=rn.randint(3,10), death_function=monster_death), ai=BasicMonster())

            entities.append(monster)

    def place_items(self, room):
        global entities

        num_items = rn.randint(0,cst.MAX_ITEMS)

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
        player_x = -1
        player_y = -1

        while num_rooms < cst.MAX_ROOM:

            if num_rooms >= cst.MIN_ROOM:
                if rn.random() <= (num_rooms - cst.MIN_ROOM)/(cst.MAX_ROOM - cst.MIN_ROOM):
                    break

            carved = False

            while not carved:

                carved = True

                w = rn.randint(cst.MIN_ROOM_SIZE, cst.MAX_ROOM_SIZE)
                h = rn.randint(cst.MIN_ROOM_SIZE, cst.MAX_ROOM_SIZE)
                x = rn.randint(1, cst.MAP_WIDTH - w - 1)
                y = rn.randint(1, cst.MAP_HEIGHT - h - 1)

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
                player_x = new_x
                player_y = new_y

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

        return player_x, player_y