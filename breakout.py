import kivy
kivy.require('1.9.1')
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Callback
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, BoundedNumericProperty
from kivy.uix.label import Label
from kivy.vector import Vector
from random import randint, choice
from time import sleep
from functools import partial

'''
        
    Widget: id: walls
        
        Collider:
            size: root.width, 100
            pos: 0, root.height
        
        Collider:
            size: 100, root.height
            pos: 0 - self.width, 0
        
        Collider:
            size: 100, root.height
            pos: root.width, 0
'''

#Set window size
Window.size = (800, 600)

#Class for holding level data
class BrickManager():
    
    #Each number holds the strength of the block in each row
    levels = [
            [3,2,1,0,3,2,1,0], # Lvl 0
            [0,0,0,0,0,0,0,0] # Lvl 1
            ]

#Level() holds more advanced properties of a level, that I can't think of a way to implement.
'''        
class Level():
    

    def __init__(self, rows=3, config='center', *bricks):
        if config == 'center':
'''


class Brick(Widget):
    
    color_code = [
                (1, 0, 0),
                (0, 1, 0),
                (0, 0, 1),
                (1, 1, 0)
                ]
    lvl = NumericProperty()

    def __init__(self, lvl=0, pos=(0, 0), **kw): # 'lvl' is for 'strength' of brick
        super().__init__(**kw)
        self.lvl = lvl
        self.pos = pos
        
        #.kv lang solves this doc string
        '''
        with self.canvas:
            self.c = Color(*self.color_code[self.lvl])
            Rectangle(pos=self.pos, size=self.size)
    
    def update_color(self):
        self.canvas.remove(self.c)
        self.c = Color(*self.color_code[self.lvl])
        self.canvas.add(self.c)
        self.canvas.ask_update()
        '''
    
    def collide_ball(self, ball, game):
        if self.collide_widget(ball):
            ball.bounce(self)
            while self.collide_widget(ball):
                #Move the ball along its new vector until it's out of the brick's collision
                #So under no condition is the ball touching the brick for more than 1 frame
                ball.pos = tuple(x + y for x, y in zip(ball.pos, ball.velocity))
            self.lvl -= 1
            if self.lvl < 0:
                game.layout.remove_widget(self)
            #Clock.schedule_once(lambda dt: self.update_color(), 1/20)
            game.score += 1
    
    
class Ball(Widget):
    velocity_error_handler = lambda x: 10 if x > 10 else -10
    velocity_x = NumericProperty(0)
    velocity_y = BoundedNumericProperty(0, min=-10, max=10, errorhandler=velocity_error_handler)
    #Revise this bit some more, not fully understood
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    
    #Function for bounce behaviour
    def bounce(self, target):
        speedup = 1.00
        #on top of target angle
        if target.x <= self.last[0] <= target.width:
            self.velocity_x *= -1
        #from side
        else:
            self.velocity_y *= -1
            
        self.velocity = Vector(*self.velocity) * speedup
    
    def move(self):
        self.last = self.center
        self.pos = Vector(*self.velocity) + self.pos
        self.next = Vector(*self.velocity) + self.pos
    
    #Note the difference from __init__(), this is for restarting game
    def init(self, screen):
        #start_pos should be set once in __init__, but I don't know how to call it in .kv
        self.start_pos = (screen.center_x, 200)
        self.center = self.start_pos
        self.velocity_y = -3
        y = abs(self.velocity_y)
        self.velocity_x = randint(-y, y)
    
class Paddle(Widget):
    
    def collide_ball(self, ball):
        if self.collide_widget(ball):
            ball.bounce(self)
    
class Breakout(Widget):
    
    score = NumericProperty()
    game_start = False
    paddle_speed = 40
    

    def __init__(self, **kw):
        super().__init__(**kw)
        #To lay bricks when game is start, also for changing levels
        #self.game_start = False
        
        #Keyboard magic
        self.keyboard = Window.request_keyboard(self.keyboard_closed, self)
        self.keyboard.bind(on_key_down=self.on_keyboard_down)
        
        #This is the container for all bricks
        #Remember to add_widget...
        self.layout = FloatLayout()
        self.add_widget(self.layout)
    
    #Figure out how the keyboard works
    def keyboard_closed(self):
        self.keyboard.unbind(on_key_down=self.on_keyboard_down)
        self.keyobard = None
        
    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'left':
            self.player.center_x -= self.paddle_speed
        elif keycode[1] == 'right':
            self.player.center_x += self.paddle_speed
    
    def update(self, dt): # the game's clock added to update to be able to control the update from the game
        #Initialization for game, game_start is now a one use variable, banished from the realm
        if not self.game_start:
            self.begin()
            self.toggle_start()
        
        #Below is fixed through unsatisfying end game condition on game end
        #game_start variable system needs to be replaced so begin() or game_over() aren't called repeatedly
        
        #Checks for end of game
        if not self.layout.children or self.ball.top < 0:
            self.ball.center = self.ball.start_pos
            self.ball.velocity = (0, 0)
            self.game_over()
            
        #Core game loop
        #Changing direction when hitting walls needs to be implemented
        self.ball.move()
        
        for brick in self.layout.children:
            brick.collide_ball(self.ball, self)
            
        self.player.collide_ball(self.ball)
        
    def game_over(self):
        #Tests if there is any bricks left/if the player loses before starting game over
        #Condition transferred to update()
        #Learn to toggle UI elements on/off with .kv lang
        over_screen = Label(text='Your score is {}'.format(str(self.score)), font_size=72, pos=self.center, size=(0, 0))
        self.add_widget(over_screen)
        #schedule_once calls a function after the 2nd argument amount of seconds
        #REGARDING THE LAMBDA PARTIAL, DON'T BUT LAMBDA IN THE FOR LOOP, ADD *args to all functions, and lambda individually
        todo_list = [self.clear_bricks, lambda dt: partial(self.remove_widget, over_screen)(), self.begin]
        for itm in todo_list:
            Clock.schedule_once(itm, 2)
        
    def begin(self, *args):
        self.lay_bricks(0) # Lvl 0
        self.ball.init(self)
        self.score = 0
        
    def toggle_start(self, *args):
        self.game_start = not self.game_start
        
    def lay_bricks(self, level):
        #List of Brick classes based on the given level
        '''
        new_bricks = []
        for i in BrickManager.levels[level]:
            new_bricks += [i] * 10
        bricks = [Brick(itm) for itm in new_bricks] # 800 * 600, 800 / 80 width == 10
        #Subwidget for holding all the bricks
        layout = Widget()
        #TO DO: Auto layout of bricks
        
        x = 0
        for layer, brick in enumerate(bricks):
            y = self.height - 100 - (layer+1) * brick.height
            
            #Assigning pos this way does not seem to work, thus the function was rewritten
            brick.pos = (x, y)
            x += brick.width
            layout.add_widget(brick)
        
        self.layout = layout
        self.add_widget(self.layout)
        '''
        #Diff between this and docstring is that the classes are instantiated much later
        
        bricks = BrickManager.levels[level]
        
        #For every layer, it creates 10 bricks with unique positions to add
        for order, itm in enumerate(bricks):
            x = 0
            y = self.height - 100 - (order+1) * Brick().height
            for _ in range(10):
                self.layout.add_widget(Brick(itm, (x, y)))
                x += Brick().width
    
    def clear_bricks(self, *args):
        for i in self.layout.children:
            self.layout.remove_widget(i)

class BreakoutApp(App):

    def build(self):
        game = Breakout()
        Clock.schedule_interval(game.update, 1/60)
        return game
        
if __name__ == '__main__':
    BreakoutApp().run()