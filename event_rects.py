import pygame
class EventRects:
    def __init__(self):
        self.respawn_rects=[
            pygame.Rect(134,0,170-134,22),
            pygame.Rect(54,36,85-54,73-36),
        ]
        self.jump_rects=[
            pygame.Rect(31,201,42-31,225-201),
            pygame.Rect(154,23,170-154,35-23),
            pygame.Rect(34,72,42-34,85-72),
            pygame.Rect(84,32,103-84,38-32),
            pygame.Rect(69,134,85-69,139-134),
            pygame.Rect(82,0,89-82,23),
        ]
        self.kill_rects=[
            pygame.Rect(8,72,18-8,80-72),
            pygame.Rect(86,95,92-86,105-93),
            pygame.Rect(86,150,93-86,160-151)
        ]
    def check_events(self,x,y):
        for rect in self.respawn_rects:
            if rect.collidepoint(x,y):
                return "respawn"
        for rect in self.jump_rects:
            if rect.collidepoint(x,y):
                return "jump"
        for rect in self.kill_rects:
            if rect.collidepoint(x,y):
                return "kill"
        return None