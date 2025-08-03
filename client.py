# client.py

# Connects to server, displays grid, handles input & game updates.
# Author : Manan + Surya

# 1. Connect to the server via socket
# 2. Display grid of locks using Tkinter
# 3. Handle user clicks on locks (send attempt message)
# 4. Show typing challenge on lock granted
# 5. Update grid + scoreboard based on server messages

# Imports
import pygame
from messages import *
from game import Game
from wpm import *
from config import *
from config import GRID_COLORS as colors
from utils import countdown_timer
from networking import ClientNetworkHandler


# Main loop:
#     receive messages
#     render grid
#     send unlock results after typing

# Cient-server:
# send message to server to claim lock
# process server message
# if success lock screen start
# or display claim fail screen
# server should send updated grid (lock not available) to all clients


pygame.init()
user_id = '779'
lock = None
#network = None

# Setup window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Clash of Typers")
font = pygame.font.SysFont(None, 28)

# helper for hud
def render_hud_text(hud_rect, left_text, center_text, right_text):
    offset = 40  # padding from edges

    # Left-aligned
    left_surface = font.render(left_text, True, colors["hud_text"])
    left_rect = left_surface.get_rect(topleft=(offset, hud_rect.centery - left_surface.get_height() // 2))
    screen.blit(left_surface, left_rect)

    # Center-aligned
    center_surface = font.render(center_text, True, colors["hud_text"])
    center_rect = center_surface.get_rect(center=hud_rect.center)
    screen.blit(center_surface, center_rect)

    # Right-aligned
    right_surface = font.render(right_text, True, colors["hud_text"])
    right_rect = right_surface.get_rect(topright=(SCREEN_WIDTH - offset, hud_rect.centery - right_surface.get_height() // 2))
    screen.blit(right_surface, right_rect)

# render main grid
def render(game, left_text, center_text, right_text, start_time):
    # draw hud at top of screen
    hud_rect = pygame.Rect(HUD_PADDING, HUD_VERT_OFFSET, SCREEN_WIDTH - (2 * HUD_PADDING), HUD_HEIGHT)
    pygame.draw.rect(screen, colors["hud_backdrop"], hud_rect)
    render_hud_text(hud_rect=hud_rect, left_text=left_text, right_text=right_text, center_text=center_text)

    # draw all locks
    for i in range(game.get_size()):
        lock = game.get_lock(i)
        row = i // GRID_ROWS             # row index in 2D
        col = i % GRID_COLS              # col index in 2D

        # lock displacements
        x = (col * CELL_SIZE) + PADDING
        y = (row * CELL_SIZE) + HUD_VERT_OFFSET + GRID_ROW_OFFSET + HUD_HEIGHT
        cell = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

        pygame.draw.rect(screen, colors[lock.difficulty], cell)
        pygame.draw.rect(screen, colors["border"], cell, width=BORDER_WIDTH)

        # display score for 3 seconds at start of game                
        elapsed_time = pygame.time.get_ticks() - start_time
        fade_duration = 2000 
        
        # gradual fade per tick
        if elapsed_time < fade_duration:
            # Fade opacity
            alpha = 255 - int((elapsed_time / fade_duration) * 255)
            alpha = max(0, alpha)

            score_text = str(lock.points)
            text_surface = font.render(score_text, True, colors["lock_text"])

            text_surface = text_surface.convert_alpha()
            text_surface.set_alpha(alpha)

            text_rect = text_surface.get_rect(center=cell.center)
            screen.blit(text_surface, text_rect)

# lock break screen helper
def render_lock_screen(lock, user_string):
    rect_v_offset = GRID_ROWS / 2.5 * (HUD_VERT_OFFSET + GRID_ROW_OFFSET + HUD_HEIGHT)
    rect_h_offset = PADDING * 1.5
    rect_height = GRID_ROWS / 1.5 * (HUD_VERT_OFFSET + GRID_ROW_OFFSET + HUD_HEIGHT)
    rect_width = SCREEN_WIDTH - 3 * PADDING

    lock_rect = pygame.Rect(rect_h_offset, rect_v_offset, rect_width, rect_height)
    pygame.draw.rect(screen, colors["hud_backdrop"], lock_rect)

    target_surface = font.render(lock.lock_string, True, colors["hud_text"])
    target_rect = target_surface.get_rect(midtop=(lock_rect.centerx, lock_rect.top + 30))
    screen.blit(target_surface, target_rect)

    typed_surface = font.render(user_string, True, colors["hud_text"])
    typed_rect = typed_surface.get_rect(midtop=(lock_rect.centerx, target_rect.bottom + 40))
    screen.blit(typed_surface, typed_rect)

# return lock object when clicking on a particular lock (else return None)
def detect_click(game, event):
    mouse_x, mouse_y = event.pos

    for i in range(game.get_size()):
        row = i // GRID_ROWS
        col = i % GRID_COLS

        x = (col * CELL_SIZE) + PADDING
        y = (row * CELL_SIZE) + HUD_HEIGHT + HUD_VERT_OFFSET + GRID_ROW_OFFSET

        if x <= mouse_x < x + CELL_SIZE and y <= mouse_y < y + CELL_SIZE:
            lock = game.get_lock(i)
            print(f"Clicked lock at ({row}, {col}) → ID {i}, points = {lock.points}")
            return lock

    return None

# start new game
def start_game():
    #network = ClientNetworkHandler(user_id=user_id)

    # Initialize client game state
    game = Game(height=GRID_ROWS, width=GRID_COLS)
    size = game.get_size()
    showing_lock_screen = False
    start_time = pygame.time.get_ticks()
    remaining_time = GAME_TIME
    total_points = 0
    total_locks = size
    remaining_locks = size

    user_string = ""
    
    # while game timer has not finished
    while remaining_time != 0 :
        if remaining_locks == 0:
            return False
        
        # HUD information
        screen.fill(colors['backdrop'])
        remaining_time = countdown_timer(start_ticks=start_time, total_seconds=GAME_TIME)

        left_text=f"Points: {total_points}" 
        center_text=f"Locks: {remaining_locks}/{total_locks}"
        right_text=f"Time: {remaining_time}s"
        
        render(game=game, left_text=left_text, right_text=right_text, center_text=center_text, start_time=start_time)

        # event parsing per tick
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # breaking a lock
            if showing_lock_screen:
                if event.type == pygame.KEYDOWN:
                    # once user releases enter key in lock break creen (submit string)
                    if event.key == pygame.K_RETURN:                
                        # TO DO: update WPM
                        user_wpm = lock.wpm_target

                        # unlock attempt handling
                        game.break_lock(lock=lock, user_string=user_string, user_wpm=user_wpm)
                        '''
                        if user_string == lock.lock_string and user_wpm >= lock.wpm_target:                     # check success locally before sending to server for string + WPM verification
                                remaining_locks -= 1
                                total_points += lock
                        
                            network.send_unlock_success(lock.lock_id, user_string, user_wpm)
                            response = network.wait_for_message_type(MSG_LOCK_CAPTURED)
                            
                        else:
                            network.send_unlock_fail(lock.lock_id)                                              # if string is invalid or WPM is unsufficient then inform server. No need for verification overhead
                            response = network.wait_for_message_type(MSG_LOCK_REVOKED)
                        
                        # wait for server broadcast for grid update regardless of unlock attempt success
                        update_response = network.wait_for_message_type(MSG_GRID_UPDATE)                    
                        
                        
                        if response and update_response:                                                        # response has been receieved
                            # if unlock is successful
                            if response.get("type") == MSG_LOCK_CAPTURED:
                                game = update_response.get("grid")
                                remaining_locks -= 1
                                total_points += response.get("points")
                            
                            # if unlock attempt fails
                            elif response.get("type") == MSG_LOCK_REVOKED:
                                game = update_response.get("grid")
                        '''
                        # reset lock and lock break screen for next attempt
                        lock = None
                        showing_lock_screen = False
                        user_string = ""

                    # delete char handling for lock break screen
                    elif event.key == pygame.K_BACKSPACE:
                        user_string = user_string[:-1]
                    elif event.unicode.isprintable():
                        user_string += event.unicode

            else:
                # lock mouse click event
                if event.type == pygame.MOUSEBUTTONDOWN:
                    lock = detect_click(game=game, event=event)
                    
                    # claim lock handling
                    if lock and game.claim_lock(user=user_id, lock=lock):                                           # check local grid first if claim is invalid (taken by other user)
                        '''
                        network.send_claim_request(lock.lock_id)                                                    # only make requests for valid claims to confirm validity from server

                        if network.wait_for_message_type([MSG_CLAIM_ACCEPTED]).get("type") == MSG_CLAIM_ACCEPTED:   # wait for server update
                            response = network.wait_for_message_type([MSG_GRID_UPDATE])
                        elif network.wait_for_message_type([MSG_CLAIM_REJECTED]).get("type") == MSG_CLAIM_REJECTED:
                            if response:
                                game.set_grid(response.get("grid"))                                                 # update grid
                                lock_screen_start = pygame.time.get_ticks()                                         # begin timer for lock break screen
                                user_string = ""                                                                    # buffer for user tying input
                                showing_lock_screen = True                                                          # display lock break screen in next iteration
                        '''
                        lock_screen_start = pygame.time.get_ticks() 
                        user_string = ""
                        showing_lock_screen = True 
        # lock break rendering call with user typed input
        if showing_lock_screen:
            if (pygame.time.get_ticks() - lock_screen_start) // 1000 < 10:                                          # quit screen after user get's 10 seconds
                render_lock_screen(lock, user_string)                       
            
            # stop rendering next iteration
            else:
                showing_lock_screen = False
                user_string = ""
                lock = None
        
        # game UI update call
        pygame.display.flip()

    return False

running = True

# TO DO: main menu
while running:
    running = start_game()

#network.close()
pygame.quit()
