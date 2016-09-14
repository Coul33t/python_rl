import constants as cst

class Object:
    def __init__(self, x, y, ch, name='DEFAULT_NAME', color=cst.white, bkg_color=None, blocks=True, max_inventory=10, class_name=None, ai=None, item=None):
        self._x = x
        self._y = y
        self._ch = ch
        self._name = name
        self._color = color
        self._bkg_color = bkg_color;
        self._blocks = blocks
        self._max_inventory = max_inventory
        self._inventory = []

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
        global map_console

        if (self._x, self._y) in visible_tiles:
            map_console.draw_char(self._x, self._y, self._ch, fg=self._color)


class BasicClass:
    def __init__(self, hp=10, stamina=10, defense=0, dmg=2, death_function=None):
        self._hp = hp
        self._max_hp = hp
        self._stamina = stamina
        self._max_stamina = stamina
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