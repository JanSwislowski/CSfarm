import time

from functions import smooth_move
from functions import cords_to_map
from mr import get_player_data

map_y=2590
map_x=-1540
map_by=-2150
map_bx=1090
mw=abs(map_x-map_bx)
mh=map_y-map_by

w,h=170,230
def cords_to_map(x,y):
    px=(x-map_x)/mw
    py=(y-map_by)/mh
    # print(px,py,"ngi")
    return int(px*w),h-int(py*h)

x, y = cords_to_map(*get_player_data()["pos"][:2])
print(x,y)