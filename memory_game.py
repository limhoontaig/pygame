import pygame
from pygame import display

# view the start screen
def display_start_screen():
    # draw a circle on the center of start button,radius 60, lineweight 5
    pygame.draw.circle(screen, WHITE, start_button.center, 60,5)

# display the screen of the game
def display_game_screen():
    print('Game start')

# confirm the click position of the start button 
def check_buttons(pos):
    global start
    if start_button.collidepoint(pos):
        start = True

# initialization
pygame.init()
screen_width = 1280
screen_height = 720
screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption('Memory Game')

# Start button
start_button = pygame.Rect(0,0,120,120)
start_button.center = (120, screen_height - 120)

# color
BLACK = (0,0,0)
WHITE = (255,255,255)

# start or not
start = False


# Game Loop
running = True # Game is running?
while running:
    click_pos = None

    # event loop
    for event in pygame.event.get(): # What event raised?
        if event.type == pygame.QUIT: # Display is closed event?
            running = False # 게임이 더이상 실행중이 아님 Game is not rinning anymore
        elif event.type == pygame.MOUSEBUTTONUP: # M
            click_pos = pygame.mouse.get_pos()
            print(click_pos)

    # fill the black all screen
    screen.fill(BLACK)

    if start:
        display_game_screen() # display of the game screen
    else:
        display_start_screen() # display of the start screen

    # display of start screen
    display_start_screen()

    # update of screen
    pygame.display.update()

    # is click position coordinate anywhere 
    if click_pos:
        check_buttons(click_pos)


# Quit the game.
pygame.quit()