import pygame
from random import *
from pygame import display

# set up correctly by the level
def setup(level):
    # How many numbers to show to the player?
    number_count = (level // 3) +5
    number_count = min(number_count, 20) # if number_count is greater than 20, then set 20

    # placement random numbers grid type on actual screen
    shuffle_grid(number_count)

#  shuffling the numbers (Most important portion of the program)
def shuffle_grid(number_count):
    rows = 5
    columns = 9
    
    cell_size = 130 # 각 Grid cell 별 가로, 세로 크기
    button_size = 110 # Grid cell 내에 실제로 그려질 버튼 크기
    screen_left_margin = 55 # 전체 스크린 왼쪽 여백
    screen_top_margin = 20 # 전체 스크린 위쪽 여백

    grid = [[0 for col in range(columns)] for row in range(rows)] # 5X 9

    number = 1 # start number 1 to number_count
    while number <= number_count:
        row_idx = randrange(0,rows)
        col_idx = randrange(0, columns)

        if grid[row_idx][col_idx] == 0:
            grid[row_idx][col_idx] = number
            number += 1

            # 현재 grid cell 위치 기준으로 x, y 위치를 구함
            center_x = screen_left_margin + (col_idx * cell_size) + (cell_size / 2)
            center_y = screen_top_margin + (row_idx * cell_size) + (cell_size / 2)

            # 숫자 버튼 만들기
            button = pygame.Rect(0, 0, button_size, button_size)
            button.center = (center_x, center_y)

            number_buttons.append(button)

    print(grid)

# view the start screen
def display_start_screen():
    # draw a circle on the center of start button,radius 60, lineweight 5
    pygame.draw.circle(screen, WHITE, start_button.center, 60,5)

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
            pygame.draw.rect(screen, WHITE, rect)
        else:
            # 실제 숫자 텍스트
            cell_text = game_font.render(str(idx), True, WHITE)
            text_rect = cell_text.get_rect(center=rect.center)
            screen.blit(cell_text, text_rect)

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

number_buttons = []

# start or not
start = False


# 게임 시작전ㅇ[ 게임 설정 함수 수행
setup(1)

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