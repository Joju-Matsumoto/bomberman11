# coding:utf-8
import arcade
import random
import math
from arcade.application import MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE

MASU = 43   #マス目(px)
MARGIN_TOP = 50
MARGIN_DOWN = 50
MARGIN_LEFT = 50
MARGIN_RIGHT = MASU*10
WIDTH, HEIGHT = 21, 13
SCREEN_WIDTH = WIDTH * MASU + MARGIN_LEFT + MARGIN_RIGHT
SCREEN_HEIGHT = HEIGHT * MASU + MARGIN_DOWN + MARGIN_TOP

DEBUG_FONT_SIZE = 9

# マップ,条件分岐等,全ての区別を統一
NO_OBJECT = -1
AIR = 0
HARD_WALL = 1
SOFT_WALL = 2
BOMB = 3
FIRE = 4
ITEM = 5
AGENT = 6

OBJECT_LIST = [AIR,SOFT_WALL,BOMB,ITEM,AGENT]

INIT_BOMB_DELAY = 3.0   # 爆弾の爆発までの時間[s]
INIT_FIRE_DELAY = 0.5   # 爆風の消滅までの時間[s]
INIT_AGENT_SPEED = 0.1  # エージェントの初期スピードクールタイム[s]
INIT_AGENT_BOMB = 1     # エージェントの初期爆弾所持数[個]
INIT_AGENT_FIRE = 2     # エージェントの初期爆弾火力[マス]
INIT_AGENT_WALL = 1     # エージェントの初期壁所持数[個]
INIT_AGENT_DEAD_COOLTIME = 6 # 死亡エージェントの初期爆弾設置クールタイム[s]
MAX_AGENT_SPEED = 0.1

# define mode
MODE_NORMAL = 1
MODE_DEBUG = -1

# define item value and touch return value
DEATH = -1
SPEED_UP = 0
BOMB_UP = 1
FIRE_UP = 2
WALL_UP = 3
NOTHING = 4

ITEM_LIST = [SPEED_UP,BOMB_UP,FIRE_UP,WALL_UP]

# define map type
MAP_FLAT = 0
MAP_RANDOM = 1

# define Direction
UP = 0
DOWN = 1
RIGHT = 2
LEFT = 3

# define AI type
PLAYER = 0
RANDOM = 1
BASIC = 2
MULTI = 3
WALKER = 4

# define agent's "next"
STAY = -1
MOVE_UP = 0
MOVE_DOWN = 1
MOVE_LEFT = 2
MOVE_RIGHT = 3
SET_BOMB = 4
SET_WALL_UP = 5
SET_WALL_DOWN = 6
SET_WALL_LEFT = 7
SET_WALL_RIGHT = 8

NEXT_LIST =[STAY,MOVE_UP,MOVE_DOWN,MOVE_LEFT,MOVE_RIGHT,SET_BOMB,SET_WALL_DOWN,SET_WALL_LEFT,SET_WALL_UP,SET_WALL_RIGHT]

# define distance_map value
FAR = 200

# Object Lists
air_list = []
hard_wall_list = []
soft_wall_list = []
bomb_list = []
fire_list = []
item_list = []
agent_list = []
break_list = []

# Object_map の要素はObject継承のクラス
object_map = [[None for i in range(WIDTH)] for j in range(HEIGHT)]

# 爆風が生じるまでの時間[s]を要素に持つマップ
fire_map = [[None for i in range(WIDTH)] for j in range(HEIGHT)]
# 爆風により破壊されるまでの時間[s]を要素に持つマップ
break_map = [[None for i in range(WIDTH)] for j in range(HEIGHT)]
# エージェントを要素に持つマップ
agent_map = [[ [] for i in range(WIDTH)] for j in range(HEIGHT)]

def pseudo_color(value):
    r = 0
    g = 0
    b = 0
    if(value<=127):
        (r, g, b) = (int(value*255/127), 255, 0)
    else:
        (r, g, b) = (255, int(255-(value-127)*255/127), 0)
    return (r,g,b)

class Delay_group:
    def __init__(self, delay):
        self.delay = delay

def agent_map_remake():
    for i in range(HEIGHT):
        for j in range(WIDTH):
            agent_map[i][j].clear()
    for agent in agent_list:
        agent_map[agent.x][agent.y].append(agent)

def fire_map_remake():
    sorted(bomb_list)
    for i in range(HEIGHT):
        for j in range(WIDTH):
            fire_map[i][j] = None
            break_map[i][j] = None
    for bomb in bomb_list:
        if(fire_map[bomb.x][bomb.y]==None):
            delay_group = Delay_group(bomb.delay)
            fire_map[bomb.x][bomb.y] = delay_group
        else:
            delay_group = fire_map[bomb.x][bomb.y]
            if(delay_group.delay > bomb.delay):
                delay_group.delay = bomb.delay

        for direction in [UP, DOWN, LEFT, RIGHT]:
            for i in range(1,bomb.fire_range+1):
                if(direction == UP):
                    x = bomb.x - i; y = bomb.y;
                elif(direction == DOWN):
                    x = bomb.x + i; y = bomb.y;
                elif(direction == LEFT):
                    x = bomb.x; y = bomb.y - i;
                elif(direction == RIGHT):
                    x = bomb.x; y = bomb.y + i;
                object_type = check(x, y)
                if(object_type == AIR):
                    if(fire_map[x][y]==None):
                        fire_map[x][y] = delay_group
                    else:
                        if(fire_map[x][y].delay > delay_group.delay):
                            fire_map[x][y] = delay_group
                elif(object_type == BOMB):
                    if(fire_map[x][y]==None):
                        fire_map[x][y] = delay_group
                    else:
                        if(fire_map[x][y].delay > delay_group.delay):
                            fire_map[x][y].delay = delay_group.delay
                        else:
                            delay_group.delay = fire_map[x][y].delay
                elif(object_type == SOFT_WALL or object_type == ITEM):
                    if(break_map[x][y]==None):
                        break_map[x][y] = delay_group
                    else:
                        if(break_map[x][y].delay > delay_group.delay):
                            break_map[x][y].delay = delay_group.delay
                    break
                else: break

def show_break_map():
    for i in range(HEIGHT):
        for j in range(WIDTH):
            if(break_map[i][j]!=None):
                print(f"{break_map[i][j].delay:.2}",end=" ")
            else:
                print("x.xx",end=" ")
        print()
    print()

def new_map(map_type = MAP_FLAT):
    air_list.clear()
    hard_wall_list.clear()
    soft_wall_list.clear()
    bomb_list.clear()
    fire_list.clear()
    item_list.clear()
    ng_map = [[0 for i in range(WIDTH)] for j in range(HEIGHT)]
    for agent in agent_list:
        ng_map[agent.x-1][agent.y-1] = 1
        ng_map[agent.x-1][agent.y] = 1
        ng_map[agent.x-1][agent.y+1] = 1
        ng_map[agent.x][agent.y-1] = 1
        ng_map[agent.x][agent.y] = 1
        ng_map[agent.x][agent.y+1] = 1
        ng_map[agent.x+1][agent.y-1] = 1
        ng_map[agent.x+1][agent.y] = 1
        ng_map[agent.x+1][agent.y+1] = 1
    for i in range(HEIGHT):
        for j in range(WIDTH):
            object_map[i][j] = None
    for i in range(HEIGHT):
        for j in range(WIDTH):
            if(i==0 or i==HEIGHT-1 or j==0 or j==WIDTH-1 or(i%2==0 and j%2==0)):
                make_hard_wall(i, j)
            else:
                make_air(i, j)
    if (map_type == MAP_RANDOM):
        for i in range(1, HEIGHT - 1):
            for j in range(1, WIDTH - 1):
                if check(i, j) == AIR:
                    if ng_map[i][j]==0:
                        if random.random() < 0.8:
                            tmp = NOTHING
                            if random.random() < 0.5:
                                tmp = random.choice(ITEM_LIST)
                            make_wall(i, j, item=tmp)

def make_fire(x,y,direction=UP,edge=False,center=False):
    """
    object_map[x][y]に Fire を設置

    ※※※ 呼び出し側は自身でdeletedを呼び出す必要あり ※※※

    """
    fire = Fire(x,y,direction=direction,edge=edge,center=center)
    fire_list.append(fire)
    object_map[x][y] = fire

def make_air(x,y):
    """
    object_map[x][y]に Air を設置

    ※※※ 呼び出し側は自身でdeletedを呼び出す必要あり ※※※

    """
    air = Air(x,y)
    air_list.append(air)
    object_map[x][y] = air

def make_wall(x,y,owner = None,item = NOTHING):
    """
    object_map[x][y]に Soft_Wall を設置
    """
    if item not in ITEM_LIST:
        item = NOTHING
    if(object_map[x][y] != None):
        object_map[x][y].deleted()
    soft_wall = Soft_Wall(x,y,owner,item)
    soft_wall_list.append(soft_wall)
    object_map[x][y] = soft_wall

def make_hard_wall(x,y):
    """
    object_map[x][y] に Hard_Wall を設置

    """
    if(object_map[x][y] != None):
        object_map[x][y].deleted()
    hard_wall = Hard_Wall(x,y)
    hard_wall_list.append(hard_wall)
    object_map[x][y] = hard_wall

def make_bomb(x,y,fire_range = 2,owner = None):
    """
    object_map[x][y]にBombを設置
    """
    if(fire_range < 2):
        fire_range = 2
    if(object_map[x][y] != None):
        object_map[x][y].deleted()
    bomb = Bomb(x,y,fire_range, owner)
    bomb_list.append(bomb)
    object_map[x][y] = bomb

def make_item(x,y,item_type = NOTHING):
    """
    object_map[x][y]に Item を設置

    ※※※ 呼び出し側は自身でdeletedを呼び出す必要あり ※※※

    """
    if(item_type in ITEM_LIST):
        item = Item(x,y,item_type)
        item_list.append(item)
        object_map[x][y] = item

def check(x, y):
    if 0 <= x and x < HEIGHT and 0 <= y and y < WIDTH:
        if(object_map[x][y]!=None):
            return object_map[x][y].type
        else:
            return NO_OBJECT
    else:
        return NO_OBJECT

class Object:
    """

    マップ( object_map[][] )に配置されるモノ

    Attributes
    ----------
    x : int
        マップ縦方向の座標
    y : int
        マップ横方向の座標
    object_type : int
        オブジェクトの種類

    """
    def __init__(self,x,y,object_type = -1):
        """

        Parameters
        ----------
        object_type : int
            オブジェクトの種類

        """
        self.x = x
        self.y = y
        self.type = object_type

    def touch(self):
        """

        オブジェクトに触れた際の処理を記述。

        """
        pass

    def damaged(self, edge=False, direction=UP):
        """

        ボムの爆発に巻き込まれた際の処理を記述。
        爆風が止まる場合は Falseを返す。

        """
        pass

    def deleted(self):
        """

        マップから消滅する際の処理を記述

        """
        pass

class Air(Object):
    """

    空気

    """
    def __init__(self,x,y):
        super().__init__(x, y, AIR)
        object_map[x][y] = self

    def damaged(self, edge=False, direction=UP):
        """

        爆発に巻き込まれた際、爆風を出現させる

        """
        make_fire(self.x, self.y,edge=edge,direction=direction)
        self.deleted()
        return True

    def deleted(self):
        """

        マップから消える際、自身を air_list から削除する

        """
        air_list.remove(self)

class Hard_Wall(Object):
    """

    堅い壁

    """
    def __init__(self,x,y):
        super().__init__(x, y, HARD_WALL)
        object_map[x][y] = self

    def damaged(self, edge=False, direction=UP):
        """

        爆発に巻き込まれた際、何も起きない。

        """
        return False

    def deleted(self):
        """

        マップから消える際、自身を hard_wall_list から削除する。

        """
        hard_wall_list.remove(self)

class Soft_Wall(Object):
    """

    壁

    """
    def __init__(self,x,y,owner = None,item_type = -1):
        """

        Parameters
        ----------
        owner : Object
            壁を設置したエージェント。デフォルト値 None
        item_type : int
            保持しているアイテムID。デフォルト値 -1

        """
        super().__init__(x, y, SOFT_WALL)
        object_map[x][y] = self
        self.owner = owner
        if(owner == None and item_type != NOTHING):
            tmp = random.randint(1,10)
            if(tmp>=8):
                item_type = random.choice(ITEM_LIST)
        self.item_type = item_type

    def damaged(self, edge=False, direction=UP):
        """

        爆発に巻き込まれた際、break_list に自信を追加

        """
        if(self not in break_list):
            break_list.append(self)
        return False

    def deleted(self):
        """

        マップから消える際、
        所有者がいる場合は、所有者の壁所持数を増やす。
        アイテムを保持している場合は、アイテムを出現させる。
        自身を soft_wall_list から削除。

        """
        if(self in break_list):
            break_list.remove(self)
        if(self.owner != None):
            self.owner.wall += 1
        if(self.item_type in ITEM_LIST):
            make_item(self.x, self.y, self.item_type)
        else:
            make_air(self.x, self.y)
        soft_wall_list.remove(self)

class Item(Object):
    """

    アイテム

    Attributes
    ----------
    item_type : int
        アイテムの種類

    """
    def __init__(self,x,y,item_type = -1):
        """

        Parameters
        ----------
        item_type : int
            アイテムの種類

        """
        super().__init__(x,y,ITEM)
        self.item_type = item_type #アイテムの種類

    def touch(self):
        """

        エージェントが触れた際、アイテムの種類を返す。

        Returns
        -------
        item_type : int
            アイテムの種類

        """
        make_air(self.x, self.y)
        item_list.remove(self)
        if self.item_type == SPEED_UP: #移動速度アップのアイテムの場合
            return SPEED_UP
        elif self.item_type == BOMB_UP: #ボム所持数アップのアイテムの場合
            return BOMB_UP
        elif self.item_type == FIRE_UP: #ボム火力アップのアイテムの場合
            return FIRE_UP
        elif self.item_type == WALL_UP: #壁所持アップアイテムの場合
            return WALL_UP

    def damaged(self, edge=False, direction=UP):
        """

        爆発に巻き込まれた際、break_list に自信を追加

        """
        if(self not in break_list):
            break_list.append(self)
        return False

    def deleted(self):
        """

        マップから消える際、自身を item_list から削除する。

        """
        if(self in break_list):
            break_list.remove(self)
        make_air(self.x, self.y)
        item_list.remove(self)

class Bomb(Object):
    """

    爆弾。ボム。

    Attributes
    ----------
    delay : float
        爆発までの時間 [秒]
    fire_range : int
        爆発時の爆風到達範囲 [マス]
    owner : Object
        所有者

    """
    def __init__(self,x,y,fire_range,owner):
        super().__init__(x,y,BOMB)
        self.delay = INIT_BOMB_DELAY #爆発までの猶予時間は2.0秒にする
        self.fire_range = fire_range
        self.owner = owner #誰がボムを置いたか記憶する

    def __lt__(self, other):
        # self < other
        return self.delay < other.delay

    def damaged(self, edge=False, direction=UP):
        """

        爆発に巻き込まれた際、爆発する。

        """
        self.explode()
        return True

    def explode(self):
        """

        爆発する。爆発範囲内にある object_map 上のオブジェクトを爆発に巻き込む

        """
        make_fire(self.x, self.y,center=True)
        bomb_list.remove(self)
        if(self.owner!=None): self.owner.bomb += 1
        for direction in [UP,DOWN,LEFT,RIGHT]:
            i = 1
            while i <= self.fire_range:
                if direction==UP:
                    tmp_x = self.x-i; tmp_y = self.y;
                    tmp_direction = DOWN
                elif direction==DOWN:
                    tmp_x = self.x+i; tmp_y = self.y;
                    tmp_direction = UP
                elif direction==LEFT:
                    tmp_x = self.x; tmp_y = self.y-i;
                    tmp_direction = RIGHT
                elif direction==RIGHT:
                    tmp_x = self.x; tmp_y = self.y+i;
                    tmp_direction = LEFT
                if i==self.fire_range:
                    edge = True
                else:
                    edge = False
                if not object_map[tmp_x][tmp_y].damaged(edge, tmp_direction):
                    break
                i += 1

    def deleted(self):
        bomb_list.remove(self)

class Fire(Object):
    """

    爆風

    """
    def __init__(self,x,y,direction=UP, center=False, edge=False):
        super().__init__(x,y,FIRE)
        self.delay = 0.5 #爆風生存時間
        self.gen_direction = direction
        self.center = center
        self.edge = edge

    def touch(self):
        """

        エージェントが触れた際、DEATH を返す

        """
        return DEATH

    def damaged(self, edge=False, direction=UP):
        """

        爆発に巻き込まれた際、爆風を生成

        """
        make_fire(self.x, self.y,edge=edge,direction=direction)
        fire_list.remove(self)
        return True

    def deleted(self):
        make_air(self.x, self.y)
        fire_list.remove(self)

class Agent(Object):
    """

    エージェント

    Attributes
    ----------
    team : int
        チーム番号
    bomb : int
        爆弾の所持数
    fire : int
        爆弾を置いた際の爆発範囲
    speed : float
        移動時に発生するクールタイム [秒]
    cooltime : float
        次に移動可能になるまでの時間 [秒]
    wall : int
        壁の所持数
    alive : bool
        生きているなら True
    dead_cooltime : float
        次に爆弾を置けるようになるまでの時間 [秒]
    AI_type : int
        エージェントの種類
    muki : int
        向いている方向

    """
    def __init__(self,x,y,team,AI_type = BASIC,muki = DOWN,bomb = INIT_AGENT_BOMB,fire = INIT_AGENT_FIRE,speed = INIT_AGENT_SPEED,wall = INIT_AGENT_WALL):
        super().__init__(x,y,AGENT)
        self.team = team
        self.bomb = bomb
        self.fire = fire
        self.speed = speed
        self.cooltime = 0
        self.wall = wall #初期の壁所持数は1個
        self.alive = True #生きているかどうか　Trueなら生きている
        self.dead_cooltime = INIT_AGENT_DEAD_COOLTIME #死亡エージェントの爆弾設置クールタイム
        # 距離マップ:自分のいる位置から各マスまでの距離
        self.distance_map = [[500 for i in range(WIDTH)] for j in range(HEIGHT)]
        self.AI_type = AI_type # PLAYER, RANDOM, BASIC, MULTI, ENEMY
        self.muki = muki # UP, DOWN, LEFT, RIGHT

    def distance_map_remake(self, cost_max = 8):
        """

        自身からの移動可能マスまでの距離を測る

        Parameters
        ----------
        cost_max : int
            移動可能チェックの上限値 [マス]

        """
        if(self.alive):
            for i in range(HEIGHT):
                for j in range(WIDTH):
                    self.distance_map[i][j] = FAR
            check_list = []
            check_list.append((self.x, self.y, 0))
            while(len(check_list)>0):
                (x, y, cost) = check_list.pop()
                self.distance_map[x][y] = cost
                for i in [UP,DOWN,LEFT,RIGHT]:
                    if(i==UP):      tmp_x = x-1; tmp_y = y;
                    elif(i==DOWN):  tmp_x = x+1; tmp_y = y;
                    elif(i==LEFT):  tmp_x = x; tmp_y = y-1;
                    elif(i==RIGHT): tmp_x = x; tmp_y = y+1;
                    if(self.x-cost_max <= tmp_x and tmp_x < self.x+cost_max and self.y-cost_max<tmp_y and tmp_y < self.y+cost_max):
                        object_type = check(tmp_x, tmp_y)
                        if(object_type==AIR or object_type==ITEM):
                            if(self.distance_map[tmp_x][tmp_y] > cost + self.speed):
                                check_list.append((tmp_x,tmp_y,cost+self.speed))
                        elif(object_type==SOFT_WALL):
                            if(self.distance_map[tmp_x][tmp_y] > cost + self.speed + INIT_BOMB_DELAY):
                                check_list.append((tmp_x,tmp_y,cost+self.speed+INIT_BOMB_DELAY))

    def think(self):
        """

        次の行動を考える

        """

    def act(self):
        """

        エージェントが行動する

        """
        if(self.AI_type == WALKER):
            tmp = random.randint(0,99)
            if(tmp >= 90):
                tmp = random.choice([UP, DOWN, LEFT, RIGHT])
                self.move(tmp)
        else:
            self.distance_map_remake()
            if(self.AI_type == RANDOM):
                tmp = random.randint(0,99)
                if(0 <= tmp and tmp <= 70):
                    pass
                elif(70 < tmp and tmp <= 76):
                    self.move(UP)
                elif(76 < tmp and tmp <= 82):
                    self.move(DOWN)
                elif(82 < tmp and tmp <= 88):
                    self.move(RIGHT)
                elif(88 < tmp and tmp <= 94):
                    self.move(LEFT)
                elif(94 < tmp and tmp <= 97):
                    self.set_bomb()
                else:
                    self.set_wall()
            elif(self.AI_type == BASIC):
                pass

    def touch(self):
        """

        生きているエージェントは、
        object_map 上のオブジェクトに触れる。
        返り値によって処理を行う。

        """
        if(self.alive):
            touch = object_map[self.x][self.y].touch()
            if(touch == DEATH):
                self.dead()
                return DEATH
            elif(touch == SPEED_UP):
                self.speed -= 0.03
                if(self.speed<MAX_AGENT_SPEED):
                    self.speed = MAX_AGENT_SPEED
            elif(touch == BOMB_UP): self.bomb += 1
            elif(touch == FIRE_UP): self.fire += 1
            elif(touch == WALL_UP): self.wall += 1

    def move(self, direction):
        """

        エージェントが移動する

        Parameters
        ----------
        direction : int
            移動方向

        """
        if(self.alive):
            if(self.cooltime == 0):
                if(direction == UP and self.can_through(self.x-1, self.y)):
                    self.x -= 1
                    self.muki = UP
                    self.cooltime = self.speed
                elif(direction == DOWN and self.can_through(self.x+1, self.y)):
                    self.x += 1
                    self.muki = DOWN
                    self.cooltime = self.speed
                elif(direction == RIGHT and self.can_through(self.x, self.y+1)):
                    self.y += 1
                    self.muki = RIGHT
                    self.cooltime = self.speed
                elif(direction == LEFT and self.can_through(self.x, self.y-1)):
                    self.y -= 1
                    self.muki = LEFT
                    self.cooltime = self.speed
        else:
            if(self.cooltime == 0):
                if(direction == UP and self.can_through(self.x-1, self.y)):
                    self.x -= 1
                    self.muki = UP
                    self.cooltime = self.speed
                elif(direction == DOWN and self.can_through(self.x+1, self.y)):
                    self.x += 1
                    self.muki = DOWN
                    self.cooltime = self.speed
                elif(direction == LEFT and self.can_through(self.x, self.y-1)):
                    self.y -= 1
                    self.muki = LEFT
                    self.cooltime = self.speed
                elif(direction == RIGHT and self.can_through(self.x, self.y+1)):
                    self.y += 1
                    self.muki = RIGHT
                    self.cooltime = self.speed

    def can_through(self,x,y): #すり抜け判定
        """

        object_map[x][y] 上のobject_typeを調べて、
        通り抜けられる場合は Trueを返す。

        """
        if(self.alive):
            object_type = check(x,y)
            if(object_type == AIR or object_type == ITEM):
                return True
            else:
                return False
        else:
            object_type = check(x,y)
            if(x != 0 and x != HEIGHT-1 and y != 0 and y != WIDTH-1):
                if(object_type != HARD_WALL):
                    return True
            return False

    def set_bomb(self):
        """

        自身の位置に、爆弾を設置する。

        """
        if self.alive == True:  # 生きている場合の処理
            if(self.bomb > 0):
                object_type = check(self.x, self.y)
                if(object_type == AIR):
                    make_bomb(self.x,self.y,self.fire,self)
                    self.bomb -= 1
                    return True
        else:  # 死んでいる場合の処理
            if(self.dead_cooltime <= 0):
                object_type = check(self.x, self.y)
                if(object_type == AIR):
                    make_bomb(self.x,self.y,self.fire,self)
                    self.dead_cooltime = INIT_AGENT_DEAD_COOLTIME
                    return True
        return False

    def set_wall(self):
        """

        自身の向いている方向に、壁を設置する。

        """
        if self.alive == True:  # 生きている場合の処理
            if(self.wall > 0):
                if(self.muki == UP):
                    object_type = check(self.x-1, self.y)
                    if(object_type == AIR):
                        make_wall(self.x-1, self.y, self)
                        self.wall -= 1
                if(self.muki == DOWN):
                    object_type = check(self.x+1, self.y)
                    if(object_type == AIR):
                        make_wall(self.x+1, self.y, self)
                        self.wall -= 1
                if(self.muki == LEFT):
                    object_type = check(self.x, self.y-1)
                    if(object_type == AIR):
                        make_wall(self.x, self.y-1, self)
                        self.wall -= 1
                if(self.muki == RIGHT):
                    object_type = check(self.x, self.y+1)
                    if(object_type == AIR):
                        make_wall(self.x, self.y+1, self)
                        self.wall -= 1
        else:   # 死んでいる場合の処理
            pass

    def dead(self): #死亡時の処理
        """

        死んだ場合は、speed を上限値にする。

        """
        self.alive = False
        self.bomb = INIT_AGENT_BOMB
        self.fire = INIT_AGENT_FIRE
        self.speed = 0.1

class Basic_Agent(Agent):
    """

    基本行動をするエージェント


    """
    def __init__(self, x, y, team):
        super().__init__(x, y, team)
        self.map_range = 8
        self.destination_x = x
        self.destination_y = y
        self.next = STAY
        self.change_destination = False
        self.prediction_map = [[0 for i in range(WIDTH)] for j in range(HEIGHT)]
        self.action_list = []
        self.danger = False
        self.target = None

    def distance_map_remake_and_set_destination(self):
        """

        自身からの距離マップを作りながら目的地を決定し次の行動を決定


        """
        self.target = None
        # 自身が危険な状態かどうか調べる
        if fire_map[self.x][self.y] != None and self.alive:
            # print("Danger")
            self.danger = True
        else:
            self.danger = False
        # 距離マップを初期化
        for i in range(HEIGHT):
            for j in range(WIDTH):
                self.distance_map[i][j] = FAR
        check_list = []
        check_list.append((self.x, self.y, 0, STAY))
        next_act = STAY
        priority = 0
        distance = 100
        self.destination_x = self.x; self.destination_y = self.y;
        # 生きている場合の距離マップ
        if self.alive:
            while(len(check_list)>0):
                (x, y, cost, first) = check_list.pop()
                tmp_first = first
                self.distance_map[x][y] = cost
                for i in [UP,DOWN,LEFT,RIGHT]:
                    if(i==UP):      tmp_x = x-1; tmp_y = y;
                    elif(i==DOWN):  tmp_x = x+1; tmp_y = y;
                    elif(i==LEFT):  tmp_x = x; tmp_y = y-1;
                    elif(i==RIGHT): tmp_x = x; tmp_y = y+1;
                    if first == STAY:
                        if i==UP:
                            tmp_first = MOVE_UP
                        elif i == DOWN:
                            tmp_first = MOVE_DOWN
                        elif i == LEFT:
                            tmp_first = MOVE_LEFT
                        else:
                            tmp_first = MOVE_RIGHT
                    if self.x-self.map_range <= tmp_x and tmp_x <= self.x+self.map_range:
                        if self.y-self.map_range <= tmp_y and tmp_y <= self.y+self.map_range:
                            object_type = check(tmp_x, tmp_y)
                            if(object_type==AIR or object_type==ITEM or object_type==FIRE):
                                if fire_map[x][y]!=None or (fire_map[x][y]==None and fire_map[tmp_x][tmp_y]==None):
                                    tmp_cost = cost + self.speed
                                else:
                                    tmp_cost = cost + self.speed + INIT_BOMB_DELAY
                                if object_type==AIR and len(agent_map[tmp_x][tmp_y])!=0:
                                    tmp_cost = cost + INIT_BOMB_DELAY/2
                                if(self.distance_map[tmp_x][tmp_y] > tmp_cost):
                                    check_list.append((tmp_x,tmp_y,tmp_cost,tmp_first))
                                    cost = tmp_cost
                                    if cost < INIT_BOMB_DELAY:# 自力で行ける距離にある
                                        if self.danger:# 自身が危険な場合は安全な場所を探す
                                            # アイテムもしくは壊れないアイテム
                                            if (object_type == AIR and len(agent_map[tmp_x][tmp_y])==0) or (object_type == ITEM and break_map[tmp_x][tmp_y]==None):
                                                if fire_map[tmp_x][tmp_y]==None:# 爆風被害無し
                                                    if priority < 200:# 被害無しが見つかっていないなら
                                                        # print("found most safe place(",tmp_x,",",tmp_y,")",cost)
                                                        priority = 200
                                                        distance = cost
                                                        self.target = object_map[tmp_x][tmp_y]
                                                        self.destination_x = tmp_x; self.destination_y = tmp_y;
                                                        next_act = tmp_first
                                                    elif priority == 200 and cost < distance:# より近い被害無しなら
                                                        # print("found most safe place(",tmp_x,",",tmp_y,")",cost)
                                                        distance = cost
                                                        self.target = object_map[tmp_x][tmp_y]
                                                        self.destination_x = tmp_x; self.destination_y = tmp_y;
                                                        next_act = tmp_first
                                                # 被害無しが見つかっていないかつ今の位置より爆風到達までの時間が長いなら
                                                elif priority < 150 and fire_map[tmp_x][tmp_y].delay > fire_map[self.x][self.y].delay:
                                                    # print("found more safe place(",tmp_x,",",tmp_y,")",cost)
                                                    priority = 150
                                                    distance = cost
                                                    self.target = object_map[tmp_x][tmp_y]
                                                    self.destination_x = tmp_x; self.destination_y = tmp_y;
                                                    next_act = tmp_first
                                        elif object_type == ITEM and break_map[tmp_x][tmp_y] == None:
                                            if priority < 90:# 現目的地の優先度がITEMより小さければ強制的に目的地変更
                                                # print("found Item (",tmp_x,",",tmp_y,")",cost)
                                                priority = 90
                                                distance = cost
                                                self.target = object_map[tmp_x][tmp_y]
                                                self.destination_x = tmp_x; self.destination_y = tmp_y;
                                                next_act = tmp_first
                                            elif priority == 90 and cost < distance:# 現目的地の優先度がITEMなら距離の近い方を優先
                                                # print("found Item (",tmp_x,",",tmp_y,")",cost)
                                                distance = cost
                                                self.target = object_map[tmp_x][tmp_y]
                                                self.destination_x = tmp_x; self.destination_y = tmp_y;
                                                next_act = tmp_first
                            elif(object_type==SOFT_WALL):
                                if(self.distance_map[tmp_x][tmp_y] > cost + self.speed + INIT_BOMB_DELAY*2):
                                    check_list.append((tmp_x,tmp_y,cost+self.speed+INIT_BOMB_DELAY*2,tmp_first))
                                    if cost < INIT_BOMB_DELAY*2:# 自力で行ける距離にある
                                        if break_map[tmp_x][tmp_y] == None:
                                            if priority < 80:# 現目的地の優先度がSOFT_WALLより小さければ強制的に目的地変更
                                                priority = 80
                                                distance = cost
                                                self.target = object_map[tmp_x][tmp_y]
                                                self.destination_x = tmp_x; self.destination_y = tmp_y;
                                                next_act = tmp_first
                                            elif priority == 80 and cost < distance:# 現目的地の優先度がSOFT_WALLなら距離の近い方を優先
                                                distance = cost
                                                self.target = object_map[tmp_x][tmp_y]
                                                self.destination_x = tmp_x; self.destination_y = tmp_y;
                                                next_act = tmp_first
                            elif(object_type == BOMB):
                                if(self.distance_map[tmp_x][tmp_y] > cost + self.speed + INIT_BOMB_DELAY*2):
                                    check_list.append((tmp_x,tmp_y,cost+self.speed+INIT_BOMB_DELAY*2,tmp_first))

                            if cost < INIT_BOMB_DELAY*2:# 自力で行ける範囲内に
                                if len(agent_map[tmp_x][tmp_y])!=0:
                                    for agent in agent_map[tmp_x][tmp_y]:
                                        if agent.team != self.team and agent.alive:# 敵エージェントがいた
                                            tmp_direction = []
                                            if check(tmp_x-2,tmp_y)==AIR and self.x-self.map_range <= tmp_x-2:
                                                tmp_direction.append((tmp_x-2,tmp_y))
                                            if check(tmp_x+2,tmp_y)==AIR and tmp_x+2 <= self.x+self.map_range:
                                                tmp_direction.append((tmp_x+2,tmp_y))
                                            if check(tmp_x,tmp_y-2)==AIR and tmp_y-2 <= self.y-self.map_range:
                                                tmp_direction.append((tmp_x,tmp_y-2))
                                            if check(tmp_x,tmp_y+2)==AIR and self.y+self.map_range <= tmp_y+2:
                                                tmp_direction.append((tmp_x,tmp_y+2))
                                            if check(tmp_x-1,tmp_y)==AIR and self.x-self.map_range <= tmp_x-1:
                                                tmp_direction.append((tmp_x-1,tmp_y))
                                            if check(tmp_x+1,tmp_y)==AIR and tmp_x+1 <= self.x+self.map_range:
                                                tmp_direction.append((tmp_x+1,tmp_y))
                                            if check(tmp_x,tmp_y-1)==AIR and tmp_y-1 <= self.y-self.map_range:
                                                tmp_direction.append((tmp_x,tmp_y-1))
                                            if check(tmp_x,tmp_y+1)==AIR and self.y+self.map_range <= tmp_y+1:
                                                tmp_direction.append((tmp_x,tmp_y+1))
                                            if len(tmp_direction) > 0:
                                                (tmp_x,tmp_y) = random.choice(tmp_direction)
                                                if priority < 100:
                                                    priority = 100
                                                    distance = cost
                                                    self.target = agent
                                                    self.destination_x = tmp_x; self.destination_y = tmp_y;
                                                    next_act = tmp_first
                                                elif priority == 100 and cost < distance:
                                                    distance = cost
                                                    self.target = agent
                                                    self.destination_x = tmp_x; self.destination_y = tmp_y;
                                                    next_act = tmp_first
        if priority < 70 or not self.alive:# 何も発見できなかった場合はagent_listのエージェントから近いエージェントを検索して近づく
            for agent in agent_list:
                if agent.team != self.team and agent.alive:
                    self.target = agent
                    d_x = agent.x - self.x; d_y = agent.y - self.y;
                    cost = abs(d_x) + abs(d_y)
                    if cost < distance:
                        if self.x%2 == 1 and self.y%2 == 1:# 十字路にいる
                            tmp = random.choice((1,2))
                            if d_x < 0:
                                if d_y < 0:
                                    if tmp == 1:
                                        next_act = MOVE_UP
                                    else:
                                        next_act = MOVE_LEFT
                                elif d_y > 0:
                                    if tmp == 1:
                                        next_act = MOVE_UP
                                    else:
                                        next_act = MOVE_RIGHT
                                else:
                                    next_act = MOVE_UP
                            elif d_x > 0:
                                if d_y < 0:
                                    if tmp == 1:
                                        next_act = MOVE_DOWN
                                    else:
                                        next_act = MOVE_LEFT
                                elif d_y > 0:
                                    if tmp == 1:
                                        next_act = MOVE_DOWN
                                    else:
                                        next_act = MOVE_RIGHT
                                else:
                                    next_act = MOVE_DOWN
                            else:
                                if d_y < 0:
                                    next_act = MOVE_LEFT
                                elif d_y > 0:
                                    next_act = MOVE_RIGHT
                        elif self.x%2 == 0:
                            if d_x <= 0:
                                next_act = MOVE_UP
                            else:
                                next_act = MOVE_DOWN
                        else:
                            if d_y <= 0:
                                next_act = MOVE_LEFT
                            else:
                                next_act = MOVE_RIGHT
        # ほんとに何も見つけられなかった場合はランダムに行動
#             if priority < 70:
#                 next_act = random.choice(NEXT_LIST)
        if not self.danger and self.alive:
            if self.target != None:
                if self.target.type == AGENT:
                    tmp = random.randint(0,100)
                    if tmp > 70:
                        next_act = random.choice([MOVE_UP,MOVE_DOWN,MOVE_LEFT,MOVE_RIGHT])
        self.next = next_act


    def predict_fire(self):
        """

        自身が爆弾を置いた際に影響の及ぶ範囲を調べる
        置いても安全 かつ 意味のある 場合は True を返す

        ※※※ 要改良 ※※※

        """
        tmp_x = self.x; tmp_y = self.y;
        for i in range(HEIGHT):
            for j in range(WIDTH):
                self.prediction_map[i][j] = 0
                if fire_map[i][j] != None:
                    self.prediction_map[i][j] = 1

        # 爆弾を置いた場合の貢献度
        contribution = 0
        self.prediction_map[self.x][self.y] = 1
        if len(agent_map[self.x][self.y]) > 1:
            for agent in agent_map[self.x][self.y]:
                if agent.team != self.team and agent.alive:
                    contribution += 10
                else:
                    if self.target == None:
                        if agent.team == self.team and agent != self:
                            contribution -= 100

        for direction in [UP, DOWN, LEFT, RIGHT]:
            for i in range(1,self.fire+1):
                if(direction == UP):
                    x = tmp_x - i; y = tmp_y;
                elif(direction == DOWN):
                    x = tmp_x + i; y = tmp_y;
                elif(direction == LEFT):
                    x = tmp_x; y = tmp_y - i;
                elif(direction == RIGHT):
                    x = tmp_x; y = tmp_y + i;
                object_type = check(x, y)
                if object_type == AIR or object_type == FIRE:
                    self.prediction_map[x][y] = 1
                elif object_type == ITEM:
                    if break_map[x][y] == None:
                        if random.randint(0,10) < 9:
                            contribution -= 10
                    break
                elif object_type == SOFT_WALL:
                    if break_map[x][y] == None:
                        contribution += 1
                    else:
                        contribution -= 1
                    break
                elif object_type == HARD_WALL:
                    break
                elif object_type == BOMB:
                    contribution += 0.5

                if len(agent_map[x][y]) != 0:
                    for agent in agent_map[x][y]:
                        if agent.alive:
                            if agent.team == self.team:
                                if random.randint(0,10) < 8:
                                    contribution -= 1
                            elif agent.team != self.team:
                                contribution += 80

        if not self.alive:
            if contribution > 20:
                return True

        if contribution >= 1:
            tmp = random.choice((3,5))
            for x in range(self.x-self.map_range,self.x+self.map_range+1):
                for y in range(self.y-self.map_range,self.y+self.map_range+1):
                    if(0 <= x and x < HEIGHT and 0 <= y and y < WIDTH):
                        if fire_map[x][y] == None and break_map[x][y]==None:
                            if self.distance_map[x][y] < self.speed * tmp and self.prediction_map[x][y] == 0:
                                # print("safety place(",x,",",y,")")
                                return True
        return False

    def think(self):
        """

        次の行動を考える

        """
        # 距離マップを再構築しつつ目的地を決定し次の行動を決める
        self.distance_map_remake_and_set_destination()
        if not self.danger:
            if self.target != None:
                if self.target.type != ITEM:
                    if self.predict_fire():
                        self.next = SET_BOMB
        elif self.target != None:
            if self.target.type == AGENT:
                if self.predict_fire():
                    self.next = SET_BOMB

    def act(self):
        """

        self.next に従って行動する

        """
#         if not self.alive:
#             self.next = STAY
        # print("Next is",end="")
        if self.next == MOVE_UP:
            if fire_map[self.x-1][self.y] == None or (self.danger and fire_map[self.x-1][self.y].delay > self.speed*2) or not self.alive:
                # print("MOVE:UP")
                self.move(UP)
        elif self.next == MOVE_DOWN:
            if fire_map[self.x+1][self.y] == None or (self.danger and fire_map[self.x+1][self.y].delay > self.speed*2) or not self.alive:
                # print("MOVE:DOWN")
                self.move(DOWN)
        elif self.next == MOVE_RIGHT:
            if fire_map[self.x][self.y+1] == None or (self.danger and fire_map[self.x][self.y+1].delay > self.speed*2) or not self.alive:
                # print("MOVE:RIGHT")
                self.move(RIGHT)
        elif self.next == MOVE_LEFT:
            if fire_map[self.x][self.y-1] == None or (self.danger and fire_map[self.x][self.y-1].delay > self.speed*2) or not self.alive:
                # print("MOVE:LEFT")
                self.move(LEFT)
        elif self.next == SET_BOMB:
            # print("SET:BOMB")
            if self.set_bomb():
                return SET_BOMB
        elif self.next == SET_WALL_UP:
            # print("SET:WALL")
            self.muki = UP
            self.set_wall()
        elif self.next == SET_WALL_DOWN:
            # print("SET:WALL")
            self.muki = DOWN
            self.set_wall()
        elif self.next == SET_WALL_LEFT:
            # print("SET:WALL")
            self.muki = LEFT
            self.set_wall()
        elif self.next == SET_WALL_RIGHT:
            # print("SET:WALL")
            self.muki = RIGHT
            self.set_wall()

    def __lt__(self, other):
        # self < other
        return self.x < other.x



class MyGame(arcade.Window):

    def __init__(self, width, height):
        super().__init__(width, height,  title="Bomberman ver.8", fullscreen = True)

        arcade.set_background_color(arcade.color.BLACK)

        # If you have sprite lists, you should create them here,
        # and set them to None
        self.player = None  #プレーヤーAgent
        self.frame_count = 0
        self.game_over = False
        self.paused = True
        self.board_sprite_list = None
        self.time_elapsed = 0.0
        self.mode = MODE_NORMAL
        self.selected_object = 0
        self.selected_value = 0
        self.mouse_tate = 0
        self.mouse_yoko = 0
        self.mouse_position_x = 0
        self.mouse_position_y = 0

#         Load sound resource
        self.sound_bgm = arcade.sound.load_sound("sound/bgm.mp3")
        self.bgm_length = 97
        self.bgm_remain = 0
        self.sound_explode = arcade.sound.load_sound("sound/explode.mp3")
        self.sound_dead = arcade.sound.load_sound("sound/damage.mp3")
        self.sound_set_bomb = arcade.sound.load_sound("sound/set_bomb.mp3")

    def new_game(self, map_type = MAP_FLAT):
        agent_list.clear()
#         player = Agent(1,1,0,PLAYER)
#         agent_list.append(player)
#         self.player = player
        basic_agent1 = Basic_Agent(1,1,0)
        agent_list.append(basic_agent1)
        basic_agent2 = Basic_Agent(1,int((WIDTH-2)/2),0)
        agent_list.append(basic_agent2)
        basic_agent3 = Basic_Agent(1,WIDTH-2,0)
        agent_list.append(basic_agent3)
        basic_agent4 = Basic_Agent(HEIGHT-2,1,1)
        agent_list.append(basic_agent4)
        basic_agent5 = Basic_Agent(HEIGHT-2,int((WIDTH-2)/2),1)
        agent_list.append(basic_agent5)
        basic_agent6 = Basic_Agent(HEIGHT-2,WIDTH-2,1)
        agent_list.append(basic_agent6)
        if(map_type == MAP_FLAT):
            new_map(MAP_FLAT)
        elif(map_type == MAP_RANDOM):
            new_map(MAP_RANDOM)
        self.time_elapsed = 0.0

    def setup(self):
        # Create your sprites and sprite lists here
        self.new_game()

        self.texture_air1 = arcade.load_texture("images/yuka1.png")
        self.texture_air2 = arcade.load_texture("images/yuka2.png")
        self.texture_bomb = arcade.load_texture("images/bomb.png")
        self.texture_soft_wall = arcade.load_texture("images/soft_wall.png")
        self.texture_hard_wall = arcade.load_texture("images/hard_wall.png")
        self.texture_bomb_up = arcade.load_texture("images/bomb_up.png")
        self.texture_fire_up = arcade.load_texture("images/fire_up.png")
        self.texture_speed_up = arcade.load_texture("images/speed_up.png")
        self.texture_wall_up = arcade.load_texture("images/wall_up.png")
        self.texture_agent1_up = arcade.load_texture("images/agent1_up.png")
        self.texture_agent1_left = arcade.load_texture("images/agent1_left.png")
        self.texture_agent1_right = arcade.load_texture("images/agent1_left.png", mirrored=True)
        self.texture_agent1_down = arcade.load_texture("images/agent1_down.png")
        self.texture_agent2_up = arcade.load_texture("images/agent2_up.png")
        self.texture_agent2_left = arcade.load_texture("images/agent2_left.png")
        self.texture_agent2_right = arcade.load_texture("images/agent2_left.png", mirrored=True)
        self.texture_agent2_down = arcade.load_texture("images/agent2_down.png")
        self.texture_shadow = arcade.load_texture("images/shadow.png")
        self.texture_ling = arcade.load_texture("images/ling.png")
        self.texture_fire_row = arcade.load_texture("images/fire_row.png")
        self.texture_fire_row_edge = arcade.load_texture("images/fire_row_edge.png")
        self.texture_fire_center = arcade.load_texture("images/fire_center.png")
        self.texture_fire = arcade.load_texture("images/fire.png")



    def draw_object(self, start_x, start_y, given_object, mul=1):
        if given_object.type == HARD_WALL:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_hard_wall)
        elif given_object.type == SOFT_WALL:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_soft_wall)
            if self.mode == MODE_DEBUG:
                item_type = given_object.item_type
                if item_type == SPEED_UP:
                    arcade.draw_texture_rectangle(start_x, start_y, MASU*mul/2, MASU*mul/2, self.texture_speed_up)
                elif item_type == BOMB_UP:
                    arcade.draw_texture_rectangle(start_x, start_y, MASU*mul/2, MASU*mul/2, self.texture_bomb_up)
                elif item_type == WALL_UP:
                    arcade.draw_texture_rectangle(start_x, start_y, MASU*mul/2, MASU*mul/2, self.texture_wall_up)
                elif item_type == FIRE_UP:
                    arcade.draw_texture_rectangle(start_x, start_y, MASU*mul/2, MASU*mul/2, self.texture_fire_up)

        elif given_object.type == BOMB:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_shadow)
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_bomb)
        elif given_object.type == FIRE:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire)
#             if given_object.center:
#                 arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire_center)
#             else:
#                 tmp_direction = given_object.gen_direction
#                 if given_object.edge:
#                     if tmp_direction == UP:
#                         arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire_row_edge,angle=270)
#                     elif tmp_direction == LEFT:
#                         arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire_row_edge,angle=0)
#                     elif tmp_direction == DOWN:
#                         arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire_row_edge,angle=90)
#                     elif tmp_direction == RIGHT:
#                         arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire_row_edge,angle=180)
#                 else:
#                     if tmp_direction in [UP,DOWN]:
#                         arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire_row,angle=90)
#                     elif tmp_direction in [LEFT,RIGHT]:
#                         arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire_row,angle=0)

        elif given_object.type == ITEM:
            item_type = given_object.item_type
            if item_type == SPEED_UP:
                arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_speed_up)
            elif item_type == BOMB_UP:
                arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_bomb_up)
            elif item_type == FIRE_UP:
                arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire_up)
            elif item_type == WALL_UP:
                arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_wall_up)
        elif given_object.type == AGENT:
            if not given_object.alive:
                mul = 0.7
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_shadow)
            if len(agent_map[given_object.x][given_object.y])>1:
                start_x += random.choice([MASU*-0.01,0,MASU*0.01])
                start_y += random.choice([MASU*-0.01,0,MASU*0.01])
            if given_object.team == 0:
                if given_object.muki == UP:
                    arcade.draw_texture_rectangle(start_x, start_y+MASU*mul/2, MASU*mul, MASU*mul*2, self.texture_agent1_up)
                elif given_object.muki == DOWN:
                    arcade.draw_texture_rectangle(start_x, start_y+MASU*mul/2, MASU*mul, MASU*mul*2, self.texture_agent1_down)
                elif given_object.muki == RIGHT:
                    arcade.draw_texture_rectangle(start_x, start_y+MASU*mul/2, MASU*mul, MASU*mul*2, self.texture_agent1_right)
                elif given_object.muki == LEFT:
                    arcade.draw_texture_rectangle(start_x, start_y+MASU*mul/2, MASU*mul, MASU*mul*2, self.texture_agent1_left)
            elif given_object.team == 1:
                if given_object.muki == UP:
                    arcade.draw_texture_rectangle(start_x, start_y+MASU*mul/2, MASU*mul, MASU*mul*2, self.texture_agent2_up)
                elif given_object.muki == DOWN:
                    arcade.draw_texture_rectangle(start_x, start_y+MASU*mul/2, MASU*mul, MASU*mul*2, self.texture_agent2_down)
                elif given_object.muki == RIGHT:
                    arcade.draw_texture_rectangle(start_x, start_y+MASU*mul/2, MASU*mul, MASU*mul*2, self.texture_agent2_right)
                elif given_object.muki == LEFT:
                    arcade.draw_texture_rectangle(start_x, start_y+MASU*mul/2, MASU*mul, MASU*mul*2, self.texture_agent2_left)
            if not given_object.alive:
                arcade.draw_texture_rectangle(start_x, start_y+MASU*mul/2, MASU*mul, MASU*mul*2, self.texture_ling)

    def draw_object_use_id(self, start_x, start_y, object_type, val=NOTHING, mul=1):
        if object_type == AIR:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_air1)
        elif object_type == BOMB:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_bomb)
        elif object_type == FIRE:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire)
        elif object_type == HARD_WALL:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_hard_wall)
        elif object_type == SOFT_WALL:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_soft_wall)
        elif object_type == ITEM:
            if val == SPEED_UP:
                arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_speed_up)
            elif val == BOMB_UP:
                arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_bomb_up)
            elif val == WALL_UP:
                arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_wall_up)
            elif val == FIRE_UP:
                arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_fire_up)
        elif object_type == AGENT:
            arcade.draw_texture_rectangle(start_x, start_y, MASU*mul, MASU*mul, self.texture_agent1_down)


    def on_draw(self):
        """
        ゲーム画面の描画
        """
        arcade.start_render()
        sorted_agent_list = sorted(agent_list)
        start_y = SCREEN_HEIGHT - MARGIN_TOP - MASU/2
        for i in range(HEIGHT):
            start_x = MARGIN_LEFT + MASU/2
            for j in range(WIDTH):
                # とりあえず床を表示
                if i != 0 and i != HEIGHT-1 and j != 0 and j != WIDTH-1:
                    if i%2 == 1 and j%2 == 1:
                        arcade.draw_texture_rectangle(start_x, start_y, MASU, MASU, self.texture_air1)
                    else:
                        arcade.draw_texture_rectangle(start_x, start_y, MASU, MASU, self.texture_air1)
                # オブジェクトを表示する
                self.draw_object(start_x, start_y, object_map[i][j])
                start_x += MASU
            start_y -= MASU

        for agent in sorted_agent_list:
            start_x = MARGIN_LEFT + MASU/2 + MASU*agent.y
            start_y = SCREEN_HEIGHT - MARGIN_TOP - MASU/2 - MASU*agent.x
            self.draw_object(start_x, start_y, agent)

        if(self.player != None):
            arcade.draw_text(f"BOMB:{self.player.bomb:.0f}  "+
                             f"SPEED:{self.player.speed:.3f}  "+
                             f"FIRE:{self.player.fire:.0f}  "+
                             f"WALL:{self.player.wall:.0f}  ", MARGIN_LEFT, SCREEN_HEIGHT-MARGIN_TOP+MASU*0.1, arcade.color.WHITE, MASU*0.5)
        # 経過時間を表示
        arcade.draw_text(f"time: {self.time_elapsed:.1f}", MARGIN_LEFT, MARGIN_DOWN-MASU, arcade.color.WHITE, MASU*0.5)
        # エージェント一覧を表示
        start_x = SCREEN_WIDTH-MARGIN_RIGHT+MASU
        start_y = SCREEN_HEIGHT-MARGIN_TOP-MASU
        for agent in agent_list:
            self.draw_object(start_x, start_y, agent, mul=0.7)
            start_y -= MASU*1.5

        if self.mode == MODE_DEBUG:
            self.draw_object_use_id(self.mouse_position_x, self.mouse_position_y, OBJECT_LIST[self.selected_object], self.selected_value,mul=0.7)
            if(0 <= self.mouse_tate and self.mouse_tate < HEIGHT and 0 <= self.mouse_yoko and self.mouse_yoko < WIDTH):
                arcade.draw_text("({:>2},{:>2})".format(self.mouse_tate,self.mouse_yoko),SCREEN_WIDTH-MARGIN_RIGHT+MASU, MASU*5, arcade.color.WHITE, MASU*0.5)
                self.draw_object(SCREEN_WIDTH-MARGIN_RIGHT+MASU*2, MASU*4, object_map[self.mouse_tate][self.mouse_yoko])

        # Call draw() on all your sprite lists below

    def update(self, delta_time):
        """

        ゲームを進行する
        ボム爆破 → 壊れるものを壊す → fire_mapを更新 → fireを消滅 →
        エージェントが行動
            (オブジェクトに触れる → 行動 → クールタイム減少

        """
        self.bgm_remain -= delta_time
        if self.bgm_remain < 0:
            self.bgm_remain = self.bgm_length
            arcade.play_sound(self.sound_bgm)
            pass
        if not(self.paused):
            self.frame_count += 1
            self.time_elapsed += delta_time
            if(len(bomb_list)>0):
                for bomb in bomb_list:
                    bomb.delay -= delta_time
                    if(bomb.delay<0):
                        bomb.explode()
                        arcade.sound.play_sound(self.sound_explode)
            if(len(break_list)>0):
                for break_object in break_list:
                    break_object.deleted()
            fire_map_remake()
            agent_map_remake()
            if(len(fire_list)>0):
                for fire in fire_list:
                    fire.delay -= delta_time
                    if(fire.delay<0):
                        fire.deleted()
            if(len(agent_list)>0):
                for agent in agent_list:
                    if agent.touch() == DEATH:
                        arcade.sound.play_sound(self.sound_dead)
                        pass
                for agent in agent_list:
                    agent.think()
                for agent in agent_list:
                    if agent.act() == SET_BOMB:
                        arcade.play_sound(self.sound_set_bomb)
                        pass
                    agent.cooltime -= delta_time
                    if(agent.cooltime < 0):
                        agent.cooltime = 0
                    if not(agent.alive):
                        agent.dead_cooltime -= delta_time
                        if(agent.dead_cooltime < 0):
                            agent.dead_cooltime = 0

    def on_key_press(self, key, key_modifiers):
        """
        Called whenever a key on the keyboard is pressed.

        For a full list of keys, see:
        http://arcade.academy/arcade.key.html
        """
        # Agent control key
        if not(self.paused):
            if(self.player != None):
                if key == arcade.key.A or key == arcade.key.LEFT:
                    self.player.muki = LEFT
                elif key == arcade.key.D or key == arcade.key.RIGHT:
                    self.player.muki = RIGHT
                elif key == arcade.key.W or key == arcade.key.UP:
                    self.player.muki = UP
                elif key == arcade.key.S or key == arcade.key.DOWN:
                    self.player.muki = DOWN
                elif key == arcade.key.SPACE:
                    self.player.set_bomb()
                elif key == arcade.key.LSHIFT:
                    self.player.set_wall()
        if key == arcade.key.Q:
            show_break_map()
        # Game control key
        if key == arcade.key.F1:
            self.paused = not(self.paused)
        elif key == arcade.key.F2:
            pass
        elif key == arcade.key.F3:
            self.mode *= -1
        elif key == arcade.key.F4:
            self.new_game(MAP_FLAT)
        elif key == arcade.key.F5:
            self.new_game(MAP_RANDOM)
        elif key == arcade.key.F11:
            self.set_fullscreen(not self.fullscreen)
        elif key == arcade.key.ESCAPE:
            exit()
        if(self.mode == MODE_DEBUG):
            if key == arcade.key.KEY_0:
                self.selected_value = 0
            elif key == arcade.key.KEY_1:
                self.selected_value = 1
            elif key == arcade.key.KEY_2:
                self.selected_value = 2
            elif key == arcade.key.KEY_3:
                self.selected_value = 3
            elif key == arcade.key.KEY_4:
                self.selected_value = 4
            elif key == arcade.key.KEY_5:
                self.selected_value = 5
            elif key == arcade.key.KEY_6:
                self.selected_value = 6
            elif key == arcade.key.KEY_7:
                self.selected_value = 7
            elif key == arcade.key.KEY_8:
                self.selected_value = 8
            elif key == arcade.key.KEY_9:
                self.selected_value = 9

    def on_key_release(self, key, key_modifiers):
        """
        Called whenever the user lets off a previously pressed key.
        """
        # Agent control key
        if not(self.paused):
            if(self.player != None):
                if key == arcade.key.A or key == arcade.key.LEFT:
                    self.player.move(LEFT)
                elif key == arcade.key.D or key == arcade.key.RIGHT:
                    self.player.move(RIGHT)
                elif key == arcade.key.W or key == arcade.key.UP:
                    self.player.move(UP)
                elif key == arcade.key.S or key == arcade.key.DOWN:
                    self.player.move(DOWN)

    def on_mouse_motion(self, x, y, delta_x, delta_y):
        """
        Called whenever the mouse moves.
        """
        self.mouse_tate = HEIGHT - 1 - math.floor((y - MARGIN_DOWN)/MASU)
        self.mouse_yoko = math.floor((x - MARGIN_LEFT)/MASU)
        self.mouse_position_x = x
        self.mouse_position_y = y

    def on_mouse_press(self, x, y, button, key_modifiers):
        """
        Called when the user presses a mouse button.
        """
        if(self.mode == MODE_DEBUG):
            if(button == MOUSE_BUTTON_LEFT):
                object_type = OBJECT_LIST[self.selected_object]
                x = self.mouse_tate; y = self.mouse_yoko;
                if(object_type == AIR):
                    if(check(x, y)!=HARD_WALL):
                        object_map[x][y].deleted()
                        make_air(x, y)
                elif(object_type == SOFT_WALL):
                    if(check(x, y)==AIR):
                        make_wall(x, y, None, self.selected_value)
                elif(object_type == ITEM):
                    if(check(x, y)==AIR):
                        make_item(x, y, self.selected_value)
                elif(object_type == BOMB):
                    if(check(x, y)==AIR):
                        make_bomb(self.mouse_tate, self.mouse_yoko, self.selected_value)
                elif(object_type == AGENT):
                    basic_agent = Basic_Agent(x,y,self.selected_value)
                    agent_list.append(basic_agent)
            elif(button == MOUSE_BUTTON_RIGHT):
                self.selected_object += 1
                if(self.selected_object >= len(OBJECT_LIST)):
                    self.selected_object = 0
            elif(button == MOUSE_BUTTON_MIDDLE):
                for agent in agent_list:
                    if(agent.x == self.mouse_tate and agent.y == self.mouse_yoko):
                        agent_list.remove(agent)

def main():
    """ Main method """
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()