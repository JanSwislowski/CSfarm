import time
import pyautogui
from functions import *
import keyboard
from graph import *
from event_rects import EventRects
from mr import get_player_data,is_player_alive
from setup import *
import threading
import pygame
steps = 5
ticks=64
pygame.init()
class player:
    def __init__(self):
        self.x=0
        self.y=0
        self.angle=0
        self.target=None
        self.graph=None
        self.r=6
        self.load_graph()
        self.prev_pos=None

        self.event_rects=EventRects()
        self.player_data=None

        self.jump_delay=1e3
        self.last_jump=0

        self.rotate_delay=1/ticks*1000*steps-10
        self.last_rotation=0

        self.stuck_pos=None
        self.last_stuck=0
        self.stack_dur=15e3 #ms

        self.last_invite=pygame.time.get_ticks()-min_s_to_milis(time_start)
        self.invite_delay=minutes_to_milis(10)
    def get_events(self):
        return self.event_rects.check_events(self.x,self.y)
    def load_graph(self):
        self.graph=Graph()
    def check_next(self):
        if self.target is None or self.target.next is None:
            # print("no target")
            return
        if distance(self.x,self.y,self.target.x,self.target.y)<self.r:
            self.target=self.target.next
            # print("next",self.target.x,self.target.y)
    def check_death(self):
        if is_player_alive()==False:
            self.spawn()
        r=15
        if distance(self.x,self.y,self.prev_pos[0],self.prev_pos[1])>r:
            # print("death")
            self.spawn()
    def set_pos(self):
        self.x,self.y=cords_to_map(*self.player_data["pos"][:2])
    def get_player_data(self):
        try:
            self.player_data=get_player_data()
        except:
            time.sleep(1)
            self.get_player_data()

    def spawn(self):
        keyboard.release('w')
        keyboard.press_and_release('x')
        time.sleep(0.5)
        self.get_player_data()
        self.set_pos()

        if self.get_events()=="respawn":
            time.sleep(0.2)
            self.spawn()
            return
        keyboard.press_and_release('3')
        self.target=self.graph.find_closest_to(self.x,self.y)
        self.prev_pos=(self.x,self.y)
    def check_jump_delay(self):
        t=pygame.time.get_ticks()
        if t-self.last_jump>self.jump_delay:
            self.last_jump=t
            return True
        return False
    def move(self):
        if not self.angle:
            return
        if self.get_events()=="jump" and self.check_jump_delay():
            keyboard.press_and_release('space')
        if self.get_events()=="kill":
            pyautogui.rightClick()
        keyboard.press('w')
    def check_rotate_delay(self,t):
        return t-self.last_rotation>self.rotate_delay
    def set_angle(self):
        t=pygame.time.get_ticks()
        if not self.check_rotate_delay(t):
            return
        self.last_rotation=t

        self.angle=self.player_data["yaw"]
        if self.angle is None:
            return
        tx=self.target.x
        ty=self.target.y
        x=self.x
        y=self.y
        angle=-get_angle(x,y,tx,ty)
        # print(angle,self.angle)
        angle_d=angle_delta(self.angle,angle)
        if angle_d>180:
            angle_d-=360
        elif angle_d<-180:
            angle_d+=360
        dist=get_dist(angle_d)

        threading.Thread(target=smooth_move, args=(-dist,steps,ticks)).start()
        # smooth_move(-dist,steps,ticks)
    def currently_stuck(self):
        r=2**2
        return (self.x-self.stuck_pos[0])**2+(self.y-self.stuck_pos[1])**2<=r
    def check_stuck(self):
        if self.stuck_pos is not None:
            if not self.currently_stuck():
                self.stuck_pos=None
                return
            if pygame.time.get_ticks()-self.last_stuck>self.stack_dur:
                self.spawn()
                return
        elif self.x==self.prev_pos[0] and self.y==self.prev_pos[1]:
            self.stuck_pos=(self.x,self.y)
            self.last_stuck=pygame.time.get_ticks()
    def invite(self):
        t=pygame.time.get_ticks()
        if t-self.last_invite>self.invite_delay:
            write_invite()
            self.last_invite=t

    def update(self):
        self.prev_pos=(self.x,self.y)
        self.get_player_data()
        self.set_pos()
        self.check_death()
        self.check_next()
        self.check_stuck()
        self.invite()
        # self.get_angle()
        self.set_angle()
        self.move()

    def run(self):
        ticks=60
        self.spawn()
        time.sleep(5)
        keyboard.press('w')
        while True:
            time.sleep(1/ticks)
            if keyboard.is_pressed('q'):
                break
            self.update()
        keyboard.release('w')



# smooth_move(dist,steps=steps)

p=player()
p.run()
# img=get_img()
# print(find_player_center(img))
# print(find_player_angle(img))

