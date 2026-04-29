import numpy as np
import time
from cs2_movement_bot import raw_mouse_move
import pyautogui

ct = np.array([30, 204, 247][::-1] + [255])
t = np.array([248, 214, 34][::-1] + [255])
#map
map_y=2590
map_x=-1540
map_by=-2150
map_bx=1090
mw=abs(map_x-map_bx)
mh=map_y-map_by

w,h=170,230

def get_angle(x1,y1,x2,y2):
    dx = x2 - x1
    dy = y2 - y1
    angle = np.arctan2(dy, dx) * 180 / np.pi
    return angle

def angle_delta(a1,a2):
    delta = (a2 - a1) % 360
    return delta

def get_dist(angle):
    # golden numbers
    one80 = 6900
    return int(angle / 180 * one80)
def cords_to_map(x,y):
    px=(x-map_x)/mw
    py=(y-map_by)/mh
    # print(px,py,"ngi")
    return int(px*w),h-int(py*h)
def write_invite():
    pyautogui.hotkey('alt', 'tab')
    pyautogui.write("@all join", interval=0.05)
    pyautogui.press("enter")
    pyautogui.hotkey('alt', 'tab')

def smooth_move(total_dx, steps=34, ticks=60):
    remaining = total_dx
    for i in range(steps):
        dx = remaining // (steps - i)  # integer division, no rounding
        remaining -= dx
        raw_mouse_move(dx, 0)
        time.sleep(1 / ticks)
def minutes_to_milis(x):
    return x*60*1000
def min_s_to_milis(x):
    return minutes_to_milis(x[0])+x[1]*1000