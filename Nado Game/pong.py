import pygame, random, sys, time, math

pygame.init()
pygame.mixer.init()

def start():
    
    size = [900, 600]
    screen = pygame.display.set_mode(size)
    
    title = "PONG: First to 11 points wins!                                          PRESS ANY KEY TO START"
    
    pygame.display.set_caption(title)
    
    white = (255,255,255)
    grey =  (169,169,169)
    black = (  0,  0,  0)

    cycle1 = 1
    cycle2 = 2
    
    clock = pygame.time.Clock()    
    
    while True:

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                else:
                    way = random.randint(1,2)
                    pygame.mixer.init()
                    beep = pygame.mixer.Sound("beep.ogg")
                    peep = pygame.mixer.Sound("peep.ogg")
                    beep.play()
                    time.sleep(0.4)
                    beep.play()
                    time.sleep(0.3)
                    peep.play()
                    play(0, 0, 250, 250, way)
            
        lPaddle = pygame.Rect((10,250),(20,100))
        rPaddle = pygame.Rect((870,250),(20,100))
        ball = pygame.Rect((440,290),(20,20))

        pygame.draw.rect(screen, white, lPaddle)
        pygame.draw.rect(screen, white, rPaddle)
        pygame.draw.rect(screen, white, ball)
        
        for i in range(0,900,50):
            line = pygame.Rect((445,i+12),(10,25))
            pygame.draw.rect(screen, grey, line)

        lSlatewha = pygame.Rect((250,30),(60,100))
        lSlatebla = pygame.Rect((260,40),(40,80))
        lSlateonea = pygame.Rect((250,30),(50,100))
        lSlatemida = pygame.Rect((260,75),(40,10))
        lSlatewhb = pygame.Rect((330,30),(60,100))
        lSlateblb = pygame.Rect((340,40),(40,80))
        lSlateoneb = pygame.Rect((330,30),(50,100))
        lSlatemidb = pygame.Rect((340,75),(40,10))
        rSlatewha = pygame.Rect((510,30),(60,100))
        rSlatebla = pygame.Rect((520,40),(40,80))
        rSlateonea = pygame.Rect((510,30),(50,100))
        rSlatemida = pygame.Rect((520,75),(40,10))
        rSlatewhb = pygame.Rect((590,30),(60,100))
        rSlateblb = pygame.Rect((600,40),(40,80))
        rSlateoneb = pygame.Rect((590,30),(50,100))
        rSlatemidb = pygame.Rect((600,75),(40,10))

        pygame.draw.rect(screen, grey, lSlatewha)
        pygame.draw.rect(screen, grey, lSlatewhb)
        pygame.draw.rect(screen, grey, rSlatewha)
        pygame.draw.rect(screen, grey, rSlatewhb)
        pygame.draw.rect(screen, black, lSlatebla)
        pygame.draw.rect(screen, black, lSlateblb)
        pygame.draw.rect(screen, black, rSlatebla)
        pygame.draw.rect(screen, black, rSlateblb)
        pygame.draw.rect(screen, grey, lSlatemidb)
        pygame.draw.rect(screen, grey, rSlatemidb)
        
        if cycle1 == 1:                       #0,1
            pygame.draw.rect(screen, black, lSlateblb)
            pygame.draw.rect(screen, black, rSlateoneb)
        
        elif cycle1 == 2:                     #8,0
            pygame.draw.rect(screen, black, rSlateoneb)
        
        elif cycle1 == 3:                     #1,8
            pygame.draw.rect(screen, black, lSlateblb)

        elif cycle1 == 4:                     #0,1
            pygame.draw.rect(screen, black, lSlateblb)
            pygame.draw.rect(screen, black, rSlateoneb)
            
        elif cycle1 == 5:                     #8,1
            pygame.draw.rect(screen, black, rSlateoneb)
            
        elif cycle1 == 6:                     #0,8
            pygame.draw.rect(screen, black, lSlateblb)

        if cycle2 == 1:                       #0,0
            pass
        
        elif cycle2 == 2:                     #1,0
            pygame.draw.rect(screen, black, lSlateonea)
        
        elif cycle2 == 3:                     #1,1
            pygame.draw.rect(screen, black, lSlateonea)
            pygame.draw.rect(screen, black, rSlateonea)
            
        elif cycle2 == 4:                     #0,1
            pygame.draw.rect(screen, black, rSlateonea)
        
        if cycle1 < 6:
            cycle1 += 1
        else:
            cycle1 = 1

        if cycle2 < 4:
            cycle2 += 1
        else:
            cycle2 = 1
            
        pygame.display.flip()
        clock.tick(30)
        
def play(p1, p2, y2, y3, way):

    size = [900, 600]
    screen = pygame.display.set_mode(size)
    
    title = "PONG: First to 11 points wins!                                            PRESS 'R' TO RESTART"
    title_pause = "                                                                                     Game paused"
    
    pygame.display.set_caption(title)
    
    white = (255,255,255)
    grey =  (169,169,169)
    black = (  0,  0,  0)
    
    x1 = 440 # Coordinates of Ball
    y1 = 290
    
    x2 = 10  # x coordinate of Left Paddle
    
    x3 = 870 # x coordinate of Right Paddle
    
    d2 = ''
    d3 = ''
    
    if way == 1:
        way = 'left'
    elif way == 2:
        way = 'right'
    
    increment = 5
        
    height = ''
    
    clock = pygame.time.Clock()    
    
    while True:

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    start()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if event.key == pygame.K_SPACE:
                    
                    loop = 0
                    
                    size = [900, 600]
                    screen = pygame.display.set_mode(size)
                    
                    pygame.display.set_caption(title_pause)
                    
                    while loop == 0:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_r:
                                    start()
                                if event.key == pygame.K_ESCAPE:
                                    pygame.quit()
                                    sys.exit(0)
                                if event.key == pygame.K_SPACE:
                                    pygame.display.set_caption(title)
                                    loop = 1

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    d2 = ''
                if event.key == pygame.K_i or event.key == pygame.K_k:
                    d3 = ''

        key = pygame.key.get_pressed()
        
        if key[pygame.K_w]:
            if y2 == 0:
                d2 = ''
            else:
                d2 = 'up'
        elif key[pygame.K_s]:
            if y2 == 500:
                d2 = ''
            else:
                d2 = 'down'
        
        if key[pygame.K_i]:
            if y3 == 0:
                d3 = ''
            else:
                d3 = 'up'
        elif key[pygame.K_k]:
            if y3 == 500:
                d3 = ''
            else:
                d3 = 'down'

        screen.fill((0,0,0))

        # Gameplay Stuffs
        
        lPaddle = pygame.Rect((x2,y2),(20,100))
        lHitbox = pygame.Rect((x2+20,y2-9),(20,138))
        rPaddle = pygame.Rect((x3,y3),(20,100))
        rHitbox = pygame.Rect((x3-20,y3-9),(20,138))
        ball = pygame.Rect((x1,y1),(20,20))
        
        pygame.draw.rect(screen, white, lPaddle)
        pygame.draw.rect(screen, white, rPaddle)
        
        for i in range(0,900,50):
            line = pygame.Rect((445,i+12),(10,25))
            pygame.draw.rect(screen, grey, line)
        
        # Blank Scoreboard
        
        lSlatewha = pygame.Rect((250,30),(60,100))
        lSlatebla = pygame.Rect((260,40),(40,80))
        lSlateonea = pygame.Rect((250,30),(50,100))
        lSlatemida = pygame.Rect((260,75),(40,10))
        
        lSlatewhb = pygame.Rect((330,30),(60,100))
        lSlateblb = pygame.Rect((340,40),(40,80))
        lSlatetopb = pygame.Rect((340,30),(40,10))
        lSlateoneb = pygame.Rect((330,30),(50,100))
        lSlatemidb = pygame.Rect((340,75),(40,10))
        lSlatebotb = pygame.Rect((340,120),(40,10))
        lSlatele1b = pygame.Rect((330,40),(10,35))
        lSlatele2b = pygame.Rect((330,85),(10,35))
        lSlateri1b = pygame.Rect((380,40),(10,35))
        lSlateri2b = pygame.Rect((380,85),(10,35))
        lSlatecmb = pygame.Rect((330,75),(10,10))
        lSlatecbb = pygame.Rect((330,120),(10,10))
        
        rSlatewha = pygame.Rect((510,30),(60,100))
        rSlatebla = pygame.Rect((520,40),(40,80))
        rSlateonea = pygame.Rect((510,30),(50,100))
        rSlatemida = pygame.Rect((520,75),(40,10))
        
        rSlatewhb = pygame.Rect((590,30),(60,100))
        rSlateblb = pygame.Rect((600,40),(40,80))
        rSlatetopb = pygame.Rect((600,30),(40,10))
        rSlateoneb = pygame.Rect((590,30),(50,100))
        rSlatemidb = pygame.Rect((600,75),(40,10))
        rSlatebotb = pygame.Rect((600,120),(40,10))
        rSlatele1b = pygame.Rect((590,40),(10,35))
        rSlatele2b = pygame.Rect((590,85),(10,35))
        rSlateri1b = pygame.Rect((640,40),(10,35))
        rSlateri2b = pygame.Rect((640,85),(10,35))
        rSlatecmb = pygame.Rect((590,75),(10,10))
        rSlatecbb = pygame.Rect((590,120),(10,10))
        
        pygame.draw.rect(screen, grey, lSlatewha)
        pygame.draw.rect(screen, black, lSlatebla)
        pygame.draw.rect(screen, grey, lSlatemida)
        
        pygame.draw.rect(screen, grey, lSlatewhb)
        pygame.draw.rect(screen, black, lSlateblb)
        pygame.draw.rect(screen, grey, lSlatemidb)
        
        pygame.draw.rect(screen, grey, rSlatewha)
        pygame.draw.rect(screen, black, rSlatebla)
        pygame.draw.rect(screen, grey, rSlatemida)
        
        pygame.draw.rect(screen, grey, rSlatewhb)
        pygame.draw.rect(screen, black, rSlateblb)
        pygame.draw.rect(screen, grey, rSlatemidb)
        
        # Display Score
        
        if p1 < 10:
            pygame.draw.rect(screen, black, lSlatebla)
            if p1 == 0:
                pygame.draw.rect(screen, black, lSlateblb)
            elif p1 == 1:
                pygame.draw.rect(screen, black, lSlateoneb)
            elif p1 == 2:
                pygame.draw.rect(screen, black, lSlatele1b)
                pygame.draw.rect(screen, black, lSlateri2b)
            elif p1 == 3:
                pygame.draw.rect(screen, black, lSlatele1b)
                pygame.draw.rect(screen, black, lSlatele2b)
            elif p1 == 4:
                pygame.draw.rect(screen, black, lSlatetopb)
                pygame.draw.rect(screen, black, lSlatele2b)
                pygame.draw.rect(screen, black, lSlatebotb)
                pygame.draw.rect(screen, black, lSlatecbb)
            elif p1 == 5:
                pygame.draw.rect(screen, black, lSlateri1b)
                pygame.draw.rect(screen, black, lSlatele2b)
            elif p1 == 6:
                pygame.draw.rect(screen, black, lSlateri1b)
            elif p1 == 7:
                pygame.draw.rect(screen, black, lSlateblb)
                pygame.draw.rect(screen, black, lSlatele1b)
                pygame.draw.rect(screen, black, lSlatele2b)
                pygame.draw.rect(screen, black, lSlatebotb)
                pygame.draw.rect(screen, black, lSlatecmb)
                pygame.draw.rect(screen, black, lSlatecbb)
            elif p1 == 8:
                pass
            elif p1 == 9:
                pygame.draw.rect(screen, black, lSlatele2b)
                pygame.draw.rect(screen, black, lSlatebotb)
                pygame.draw.rect(screen, black, lSlatecbb)
        elif p1 == 10:
            pygame.draw.rect(screen, black, lSlateonea)
            pygame.draw.rect(screen, black, lSlateblb)
        elif p1 == 11:
            pygame.draw.rect(screen, black, lSlateonea)
            pygame.draw.rect(screen, black, lSlateoneb)
                
        if p2 < 10:
            pygame.draw.rect(screen, black, rSlatebla)
            if p2 == 0:
                pygame.draw.rect(screen, black, rSlateblb)
            elif p2 == 1:
                pygame.draw.rect(screen, black, rSlateoneb)
            elif p2 == 2:
                pygame.draw.rect(screen, black, rSlatele1b)
                pygame.draw.rect(screen, black, rSlateri2b)
            elif p2 == 3:
                pygame.draw.rect(screen, black, rSlatele1b)
                pygame.draw.rect(screen, black, rSlatele2b)
            elif p2 == 4:
                pygame.draw.rect(screen, black, rSlatetopb)
                pygame.draw.rect(screen, black, rSlatele2b)
                pygame.draw.rect(screen, black, rSlatebotb)
                pygame.draw.rect(screen, black, rSlatecbb)
            elif p2 == 5:
                pygame.draw.rect(screen, black, rSlateri1b)
                pygame.draw.rect(screen, black, rSlatele2b)
            elif p2 == 6:
                pygame.draw.rect(screen, black, rSlateri1b)
            elif p2 == 7:
                pygame.draw.rect(screen, black, rSlateblb)
                pygame.draw.rect(screen, black, rSlatele1b)
                pygame.draw.rect(screen, black, rSlatele2b)
                pygame.draw.rect(screen, black, rSlatebotb)
                pygame.draw.rect(screen, black, rSlatecmb)
                pygame.draw.rect(screen, black, rSlatecbb)
            elif p2 == 8:
                pass
            elif p2 == 9:
                pygame.draw.rect(screen, black, rSlatele2b)
                pygame.draw.rect(screen, black, rSlatebotb)
                pygame.draw.rect(screen, black, rSlatecbb)
        elif p2 == 10:
            pygame.draw.rect(screen, black, rSlateonea)
            pygame.draw.rect(screen, black, rSlateblb)
        elif p2 == 11:
            pygame.draw.rect(screen, black, rSlateonea)
            pygame.draw.rect(screen, black, rSlateoneb)

        pygame.draw.rect(screen, white, ball)

        if p1 == 11 or p2 == 11:
            finish(p1,p2,y2,y3)
        
        if d2 == '':
            pass
        elif d2 == 'up':
            if y2 > 1:
                y2 -= 7
            else:
                d2 = ''
        elif d2 == 'down':
            if y2 < 500:
                y2 += 7
            else:
                d2 = ''

        if d3 == '':
            pass
        elif d3 == 'up':
            if y3 > 1:
                y3 -= 7
            else:
                d3 = ''
        elif d3 == 'down':
            if y3 < 500:
                y3 += 7
        
        if way == 'right':
            if x1 + 20 != x3:
                x1 += 5
            elif not(ball.colliderect(rHitbox)):
                x1 += 5
            else:
                beep = pygame.mixer.Sound("beep.ogg")
                beep.play()
                x1 -= 5
                if increment > 12:
                    increment -= random.randint(1,2)
                elif increment > 9:
                    increment -= random.randint(-1,2)
                elif increment > 4:
                    increment += random.randint(-1,2)
                else:
                    increment += random.randint(1,2)
                way = 'left'
                        
        elif way == 'left':
            if x1 - 20 != x2:
                x1 -= 5
            elif not(ball.colliderect(lHitbox)):
                x1 -= 5
            else:
                beep = pygame.mixer.Sound("beep.ogg")
                beep.play()
                x1 += 5
                if increment > 12:
                    increment -= random.randint(1,2)
                elif increment > 9:
                    increment -= random.randint(-1,2)
                elif increment > 4:
                    increment += random.randint(-1,2)
                else:
                    increment += random.randint(1,2)
                way = 'right'

        if height == '':
            if not(ball.colliderect(lHitbox) or ball.colliderect(rHitbox)):
                pass
            else:
                i = random.randint(0,1)
                if i == 0:
                    height = 'up'
                elif i == 1:
                    height = 'down'
        
        elif height == 'down':
            if y1 < 580:
                y1 += increment
            else:
                plop = pygame.mixer.Sound("plop.ogg")
                plop.play()
                y1 -= increment
                height = 'up'
                                
        elif height == 'up':
            if y1 > 0:
                y1 -= increment
            else:
                plop = pygame.mixer.Sound("plop.ogg")
                plop.play()
                y1 += increment
                height = 'down'
        
        if x1 == -20 or x1 == 900:
            
            if x1 < 0:
                p2 += 1
                time.sleep(0.5)
                play(p1,p2,y2,250,2)
                
            else:
                p1 += 1
                time.sleep(0.5)
                play(p1,p2,250,y3,1)
                
        pygame.display.flip()
        clock.tick(120)

def finish(p1,p2,y2,y3):
    
    size = [900, 600]
    screen = pygame.display.set_mode(size)
    
    if p1 > p2:
        win = 1
    else:
        win = 2
    
    title = "PONG: First to 11 points wins!                                        PRESS 'R' FOR A REMATCH!"
    
    pygame.display.set_caption(title)
    
    white = (255,255,255)
    grey = (169,169,169)
    black = (  0,  0,  0)

    d2 = ''
    d3 = ''
    
    done = False
    clock = pygame.time.Clock()
    
    while True:

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    if win == 1:
                        play(0, 0, 250, y3, 2)
                    else:
                        play(0, 0, y2, 250, 1)
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    d2 = ''
                if event.key == pygame.K_i or event.key == pygame.K_k:
                    d3 = ''

        key = pygame.key.get_pressed()
        
        if key[pygame.K_w]:
            if y2 == 0:
                d2 = ''
            else:
                d2 = 'up'
        elif key[pygame.K_s]:
            if y2 == 500:
                d2 = ''
            else:
                d2 = 'down'
        
        if key[pygame.K_i]:
            if y3 == 0:
                d3 = ''
            else:
                d3 = 'up'
        elif key[pygame.K_k]:
            if y3 == 500:
                d3 = ''
            else:
                d3 = 'down'

        screen.fill((0,0,0))
        
        lPaddle = pygame.Rect((10,y2),(20,100))
        rPaddle = pygame.Rect((870,y3),(20,100))
        
        pygame.draw.rect(screen, white, lPaddle)
        pygame.draw.rect(screen, white, rPaddle)

        for i in range(0,900,50):
            line = pygame.Rect((445,i+12),(10,25))
            pygame.draw.rect(screen, grey, line)        

        if p1 > p2:
            x = 0
        else:
            x = 425
            
        pi = math.pi
        
        pygame.draw.line(screen, grey, [175+x,250], [150+x,220], 5)              # Y
        pygame.draw.line(screen, grey, [175+x,250], [200+x,220], 5)
        pygame.draw.line(screen, grey, [175+x,250], [175+x,290], 5)
        
        pygame.draw.circle(screen, grey, [235+x, 255], 36, 5)                    # O
        
        pygame.draw.arc(screen, grey, [275+x, 155, 60, 135],  pi, 3 * pi / 2, 5) # U
        pygame.draw.arc(screen, grey, [275+x, 155, 60, 135], 3 * pi / 2, 2 * pi, 5)

        pygame.draw.line(screen, grey, [150+x,320], [165+x,390], 5)              # W
        pygame.draw.line(screen, grey, [165+x,390], [175+x,320], 5)
        pygame.draw.line(screen, grey, [175+x,320], [185+x,390], 5)
        pygame.draw.line(screen, grey, [185+x,390], [200+x,320], 5)

        pygame.draw.line(screen, grey, [230+x,320], [230+x,390], 5)              # I
        
        pygame.draw.line(screen, grey, [265+x,320], [265+x,390], 5)              # N
        pygame.draw.line(screen, grey, [265+x,320], [300+x,390], 5)
        pygame.draw.line(screen, grey, [300+x,320], [300+x,390], 5)
        
        pygame.draw.line(screen, grey, [325+x,320], [325+x,370], 5)              # !
        pygame.draw.circle(screen, grey, [327+x,385], 5, 5)
            
        # Blank Scoreboard
        
        lSlatewha = pygame.Rect((250,30),(60,100))
        lSlatebla = pygame.Rect((260,40),(40,80))
        lSlateonea = pygame.Rect((250,30),(50,100))
        lSlatemida = pygame.Rect((260,75),(40,10))
        
        lSlatewhb = pygame.Rect((330,30),(60,100))
        lSlateblb = pygame.Rect((340,40),(40,80))
        lSlatetopb = pygame.Rect((340,30),(40,10))
        lSlateoneb = pygame.Rect((330,30),(50,100))
        lSlatemidb = pygame.Rect((340,75),(40,10))
        lSlatebotb = pygame.Rect((340,120),(40,10))
        lSlatele1b = pygame.Rect((330,40),(10,35))
        lSlatele2b = pygame.Rect((330,85),(10,35))
        lSlateri1b = pygame.Rect((380,40),(10,35))
        lSlateri2b = pygame.Rect((380,85),(10,35))
        lSlatecmb = pygame.Rect((330,75),(10,10))
        lSlatecbb = pygame.Rect((330,120),(10,10))
        
        rSlatewha = pygame.Rect((510,30),(60,100))
        rSlatebla = pygame.Rect((520,40),(40,80))
        rSlateonea = pygame.Rect((510,30),(50,100))
        rSlatemida = pygame.Rect((520,75),(40,10))
        
        rSlatewhb = pygame.Rect((590,30),(60,100))
        rSlateblb = pygame.Rect((600,40),(40,80))
        rSlatetopb = pygame.Rect((600,30),(40,10))
        rSlateoneb = pygame.Rect((590,30),(50,100))
        rSlatemidb = pygame.Rect((600,75),(40,10))
        rSlatebotb = pygame.Rect((600,120),(40,10))
        rSlatele1b = pygame.Rect((590,40),(10,35))
        rSlatele2b = pygame.Rect((590,85),(10,35))
        rSlateri1b = pygame.Rect((640,40),(10,35))
        rSlateri2b = pygame.Rect((640,85),(10,35))
        rSlatecmb = pygame.Rect((590,75),(10,10))
        rSlatecbb = pygame.Rect((590,120),(10,10))
        
        pygame.draw.rect(screen, grey, lSlatewha)
        pygame.draw.rect(screen, black, lSlatebla)
        pygame.draw.rect(screen, grey, lSlatemida)
        
        pygame.draw.rect(screen, grey, lSlatewhb)
        pygame.draw.rect(screen, black, lSlateblb)
        pygame.draw.rect(screen, grey, lSlatemidb)
        
        pygame.draw.rect(screen, grey, rSlatewha)
        pygame.draw.rect(screen, black, rSlatebla)
        pygame.draw.rect(screen, grey, rSlatemida)
        
        pygame.draw.rect(screen, grey, rSlatewhb)
        pygame.draw.rect(screen, black, rSlateblb)
        pygame.draw.rect(screen, grey, rSlatemidb)
        
        # Display Score
        
        if p1 < 10:
            pygame.draw.rect(screen, black, lSlatebla)
            if p1 == 0:
                pygame.draw.rect(screen, black, lSlateblb)
            elif p1 == 1:
                pygame.draw.rect(screen, black, lSlateoneb)
            elif p1 == 2:
                pygame.draw.rect(screen, black, lSlatele1b)
                pygame.draw.rect(screen, black, lSlateri2b)
            elif p1 == 3:
                pygame.draw.rect(screen, black, lSlatele1b)
                pygame.draw.rect(screen, black, lSlatele2b)
            elif p1 == 4:
                pygame.draw.rect(screen, black, lSlatetopb)
                pygame.draw.rect(screen, black, lSlatele2b)
                pygame.draw.rect(screen, black, lSlatebotb)
                pygame.draw.rect(screen, black, lSlatecbb)
            elif p1 == 5:
                pygame.draw.rect(screen, black, lSlateri1b)
                pygame.draw.rect(screen, black, lSlatele2b)
            elif p1 == 6:
                pygame.draw.rect(screen, black, lSlateri1b)
            elif p1 == 7:
                pygame.draw.rect(screen, black, lSlateblb)
                pygame.draw.rect(screen, black, lSlatele1b)
                pygame.draw.rect(screen, black, lSlatele2b)
                pygame.draw.rect(screen, black, lSlatebotb)
                pygame.draw.rect(screen, black, lSlatecmb)
                pygame.draw.rect(screen, black, lSlatecbb)
            elif p1 == 8:
                pass
            elif p1 == 9:
                pygame.draw.rect(screen, black, lSlatele2b)
                pygame.draw.rect(screen, black, lSlatebotb)
                pygame.draw.rect(screen, black, lSlatecbb)
        elif p1 == 10:
            pygame.draw.rect(screen, black, lSlateonea)
            pygame.draw.rect(screen, black, lSlateblb)
        elif p1 == 11:
            pygame.draw.rect(screen, black, lSlateonea)
            pygame.draw.rect(screen, black, lSlateoneb)
                
        if p2 < 10:
            pygame.draw.rect(screen, black, rSlatebla)
            if p2 == 0:
                pygame.draw.rect(screen, black, rSlateblb)
            elif p2 == 1:
                pygame.draw.rect(screen, black, rSlateoneb)
            elif p2 == 2:
                pygame.draw.rect(screen, black, rSlatele1b)
                pygame.draw.rect(screen, black, rSlateri2b)
            elif p2 == 3:
                pygame.draw.rect(screen, black, rSlatele1b)
                pygame.draw.rect(screen, black, rSlatele2b)
            elif p2 == 4:
                pygame.draw.rect(screen, black, rSlatetopb)
                pygame.draw.rect(screen, black, rSlatele2b)
                pygame.draw.rect(screen, black, rSlatebotb)
                pygame.draw.rect(screen, black, rSlatecbb)
            elif p2 == 5:
                pygame.draw.rect(screen, black, rSlateri1b)
                pygame.draw.rect(screen, black, rSlatele2b)
            elif p2 == 6:
                pygame.draw.rect(screen, black, rSlateri1b)
            elif p2 == 7:
                pygame.draw.rect(screen, black, rSlateblb)
                pygame.draw.rect(screen, black, rSlatele1b)
                pygame.draw.rect(screen, black, rSlatele2b)
                pygame.draw.rect(screen, black, rSlatebotb)
                pygame.draw.rect(screen, black, rSlatecmb)
                pygame.draw.rect(screen, black, rSlatecbb)
            elif p2 == 8:
                pass
            elif p2 == 9:
                pygame.draw.rect(screen, black, rSlatele2b)
                pygame.draw.rect(screen, black, rSlatebotb)
                pygame.draw.rect(screen, black, rSlatecbb)
        elif p2 == 10:
            pygame.draw.rect(screen, black, rSlateonea)
            pygame.draw.rect(screen, black, rSlateblb)
        elif p2 == 11:
            pygame.draw.rect(screen, black, rSlateonea)
            pygame.draw.rect(screen, black, rSlateoneb)
            
        if d2 == '':
            pass
        elif d2 == 'up':
            if y2 > 1:
                y2 -= 10
            else:
                d2 = ''
        elif d2 == 'down':
            if y2 < 500:
                y2 += 10
            else:
                d2 = ''

        if d3 == '':
            pass
        elif d3 == 'up':
            if y3 > 1:
                y3 -= 10
            else:
                d3 = ''
        elif d3 == 'down':
            if y3 < 500:
                y3 += 10
        
        pygame.display.flip()
        clock.tick(60)

start()