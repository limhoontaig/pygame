import pygame
from pygame import display

# view the start screen
def display_start_screen():
    pygame.draw.circle(screen, WHITE, start_button.center, 60,5)


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


# Game Loop
running = True # Game is running?
while running:
    # event loop
    for event in pygame.event.get(): # What event raised?
        if event.type == pygame.QUIT: # Display is closed event?
            running = False # 게임이 더이상 실행중이 아님 Game is not rinning anymore

    # fill the black all screen
    screen.fill(BLACK)

    # display of start screen
    display_start_screen()

    # update of screen
    pygame.display.update()


# Quit the game.
pygame.quit()