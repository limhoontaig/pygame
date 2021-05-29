import pygame
from random import *

# set up correctly by the level
def setup(level):
    # How long to show the numbers to the player
    global display_time
    display_time = 5 - (level // 3)
    display_time = max (display_time, 1)
    
    # How many numbers to show to the player?
    number_count = (level // 3) +5
    number_count = min(number_count, 20) # if number_count is greater than 20, then set 20

    # placement random numbers grid type on actual screen
    shuffle_grid(number_count)

#  shuffling the numbers (Most important portion of the program)
def shuffle_grid(number_count):
    rows = 5
    columns = 9
    
    cell_size = 130 # dimension of width and length of each Grid cell
    button_size = 110 # Actual button size to draw in Grid cell
    screen_left_margin = 55 # Left margin of the screen
    screen_top_margin = 20 # Top margin of the screen

    grid = [[0 for col in range(columns)] for row in range(rows)] # 5X 9

    number = 1 # start number 1 to number_count
    while number <= number_count:
        row_idx = randrange(0,rows)
        col_idx = randrange(0, columns)

        if grid[row_idx][col_idx] == 0:
            grid[row_idx][col_idx] = number
            number += 1

            # compute the x, y location of the current grid cell
            center_x = screen_left_margin + (col_idx * cell_size) + (cell_size / 2)
            center_y = screen_top_margin + (row_idx * cell_size) + (cell_size / 2)

            # make a number button
            button = pygame.Rect(0, 0, button_size, button_size)
            button.center = (center_x, center_y)

            number_buttons.append(button)

# view the start screen
def display_start_screen():
    # draw a circle on the center of start button,radius 60, lineweight 5
    pygame.draw.circle(screen, WHITE, start_button.center, 60,5)

    msg = game_font.render(f'{curr_level}', True, WHITE)
    msg_rect = msg.get_rect(center=start_button.center)
    screen.blit(msg, msg_rect)


# display the screen of the game
def display_game_screen():
    global hidden

    if not hidden:
        elapsed_time = (pygame.time.get_ticks() - start_ticks) / 1000 # ms -> sec
        if elapsed_time > display_time:
            hidden = True

    for idx, rect in enumerate(number_buttons, start=1):
        if hidden: # 숨김 처리
            # 버튼 사각형 그리기
            pygame.draw.rect(screen, GRAY, rect)
        else:
            # 실제 숫자 텍스트
            cell_text = game_font.render(str(idx), True, WHITE)
            text_rect = cell_text.get_rect(center=rect.center)
            screen.blit(cell_text, text_rect)

# confirm the click position of the start button 
def check_buttons(pos):
    global start, start_ticks

    if start:
        check_number_buttons(pos)
    elif start_button.collidepoint(pos):
        start = True
        start_ticks = pygame.time.get_ticks() # start of the timer (stored the current time)

def check_number_buttons(pos):
    global start, hidden, curr_level

    for button in number_buttons:
        if button.collidepoint(pos):
            if button == number_buttons[0]:
                del number_buttons[0]
                if not hidden:
                    hidden = True # hide the number
            else: # clicked the wrong number
                game_over()
            break

    # if all numbers are correct selection, then up the level of the game to start
    if len(number_buttons) == 0:
        start = False
        hidden = False
        curr_level += 1
        setup(curr_level)

# Treated the game over, to show thw message
def game_over():
    global running
    running = False

    msg = game_font.render(f'Your level is {curr_level}', True,WHITE)
    msg_rect = msg.get_rect(center=(screen_width / 2, screen_height / 2))

    screen.fill(BLACK)
    screen.blit(msg, msg_rect)


# initialization
pygame.init()
pygame.font.init()
screen_width = 1280
screen_height = 720
screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption('Memory Game')
game_font = pygame.font.Font(None, 100) # define the font 

# Start button
start_button = pygame.Rect(0,0,120,120)
start_button.center = (120, screen_height - 120)

# color
BLACK = (0,0,0)
WHITE = (255,255,255)
GRAY = (50,50,50)

number_buttons = [] # Buttons to push by player
curr_level = 1 # current level
display_time = None # the time of the showing the number
start_ticks = None # compute the time (stored the current time)

# start or not
start = False

# to show the number or not (number one clicked or over the time to show)
hidden = False

# run a init function before the game start 게임 시작전ㅇ[ 게임 설정 함수 수행
setup(curr_level)

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

    # fill the black all screen
    screen.fill(BLACK)

    # display of start screen

    if start:
        display_game_screen() # display of the game screen
    else:
        display_start_screen() # display of the start screen

    # if has it a clicked position (clicked anywhere)
    if click_pos:
        check_buttons(click_pos)

    # update the screen
    pygame.display.update()

# to show the 5 seconds
pygame.time.delay(5000)

# Quit the game.
pygame.quit()