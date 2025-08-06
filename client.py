# client.py

# Connects to server, displays grid, handles input & game updates.
# Author : Manan + Surya

# 1. Connect to the server via socket
# 2. Display grid of locks using Tkinter
# 3. Handle user clicks on locks (send attempt message)
# 4. Show typing challenge on lock granted
# 5. Update grid + scoreboard based on server messages

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

# client_main.py
# Clean version of client.py integrated with networking
import pygame
from config import *
from config import GRID_COLORS as colors
from utils import countdown_timer
from game import *
from networking import ClientNetwork
from messages import *

# game
pygame.init()
clock = pygame.time.Clock()

# client info
user_id = '779'
icon = '★'

# main rendering screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Clash of Typers")
font = pygame.font.SysFont(None, 28)

small_font = pygame.font.SysFont(None, 20)

# Key state tracking for better input handling
key_states = {}

# client side networking handler
network = ClientNetwork(user_id)

    # Right-aligned
    right_surface = font.render(right_text, True, colors["hud_text"])
    right_rect = right_surface.get_rect(topright=(SCREEN_WIDTH - offset, hud_rect.centery - right_surface.get_height() // 2))
    screen.blit(right_surface, right_rect)

# Enhanced scoreboard rendering
def render_detailed_scoreboard(total_points, remaining_locks, total_locks, remaining_time, current_wpm=None):
    # Main HUD
    hud_rect = pygame.Rect(HUD_PADDING, HUD_VERT_OFFSET, SCREEN_WIDTH - (2 * HUD_PADDING), HUD_HEIGHT)
    pygame.draw.rect(screen, colors["hud_backdrop"], hud_rect)
    
    # Enhanced HUD text with more details
    left_text = f"Points: {total_points}"
    center_text = f"Locks: {remaining_locks}/{total_locks}"
    right_text = f"Time: {remaining_time}s"
    
    if current_wpm:
        center_text += f" | WPM: {current_wpm}"
    
    render_hud_text(hud_rect=hud_rect, left_text=left_text, right_text=right_text, center_text=center_text)
    
    # Additional stats below HUD
    stats_rect = pygame.Rect(HUD_PADDING, HUD_VERT_OFFSET + HUD_HEIGHT + 5, SCREEN_WIDTH - (2 * HUD_PADDING), 30)
    pygame.draw.rect(screen, colors["hud_backdrop"], stats_rect)  # Use red background like main HUD
    
    # Progress text - positioned at top of stats bar
    progress_text = f"Progress: {total_locks - remaining_locks}/{total_locks}"
    progress_surface = small_font.render(progress_text, True, colors["hud_text"])
    progress_text_rect = progress_surface.get_rect(midleft=(HUD_PADDING + 10, stats_rect.top + 8))
    screen.blit(progress_surface, progress_text_rect)
    
    # Progress bar for locks - shows COMPLETED progress (fills up as you break locks)
    completed_locks = total_locks - remaining_locks
    progress_width = (SCREEN_WIDTH - (2 * HUD_PADDING) - 20) * (completed_locks / total_locks)
    progress_rect = pygame.Rect(HUD_PADDING + 10, stats_rect.bottom - 8, progress_width, 4)
    pygame.draw.rect(screen, colors["hud_text"], progress_rect)

# render main grid
def render(game, left_text, center_text, right_text, start_time, total_points, remaining_locks, total_locks, remaining_time, current_wpm=None):
    # draw enhanced hud at top of screen
    render_detailed_scoreboard(total_points, remaining_locks, total_locks, remaining_time, current_wpm)

    # draw all locks
    for i in range(game.get_size()):
        lock = game.get_lock(i)
        row = i // GRID_ROWS             # row index in 2D
        col = i % GRID_COLS              # col index in 2D

        # lock displacements
        x = (col * CELL_SIZE) + PADDING
        y = (row * CELL_SIZE) + HUD_VERT_OFFSET + GRID_ROW_OFFSET + HUD_HEIGHT + 35  # +35 for stats bar
        cell = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

        # Show different colors for broken vs available locks
        if lock.broken:
            pygame.draw.rect(screen, colors["finished"], cell)  # Gray for finished
        else:
            pygame.draw.rect(screen, colors[lock.difficulty], cell)

        pygame.draw.rect(screen, colors["border"], cell, width=BORDER_WIDTH)
        

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
    rect_v_offset = GRID_ROWS / 2.5 * (HUD_VERT_OFFSET + GRID_ROW_OFFSET + HUD_HEIGHT + 35)  # +35 for stats bar
    rect_h_offset = PADDING * 1.5
    rect_height = GRID_ROWS / 1.5 * (HUD_VERT_OFFSET + GRID_ROW_OFFSET + HUD_HEIGHT + 35)
    rect_width = SCREEN_WIDTH - 3 * PADDING

    lock_rect = pygame.Rect(rect_h_offset, rect_v_offset, rect_width, rect_height)

    pygame.draw.rect(screen, colors["hud_backdrop"], lock_rect)
    
    wrapped_text = wrap_text(lock.lock_string, font, lock_rect.width - 2 * padding)
    y = lock_rect.top + 30
    
    for line in wrapped_text:
        rendered = font.render(line, True, colors["hud_text"])
        screen.blit(rendered, (lock_rect.centerx - rendered.get_width() // 2, y))
        
        y += rendered.get_height() + 5
    
    typed_surface = font.render(user_input, True, colors["hud_text"])
    screen.blit(typed_surface, typed_surface.get_rect(midtop=(lock_rect.centerx, y + text_gap)))

    # Target string to type
    target_surface = font.render(lock.lock_string, True, colors["hud_text"])
    target_rect = target_surface.get_rect(midtop=(lock_rect.centerx, lock_rect.top + 30))
    screen.blit(target_surface, target_rect)

    # User typed string
    typed_surface = font.render(user_string, True, colors["hud_text"])
    typed_rect = typed_surface.get_rect(midtop=(lock_rect.centerx, target_rect.bottom + 40))
    screen.blit(typed_surface, typed_rect)
    
    # WPM target display
    wpm_text = f"Target WPM: {lock.wpm_target}"
    wpm_surface = small_font.render(wpm_text, True, colors["hud_text"])
    wpm_rect = wpm_surface.get_rect(midtop=(lock_rect.centerx, typed_rect.bottom + 20))
    screen.blit(wpm_surface, wpm_rect)
    
    # Instructions
    instruction_text = "Type the string above and press ENTER to submit"
    instruction_surface = small_font.render(instruction_text, True, colors["hud_text"])
    instruction_rect = instruction_surface.get_rect(midtop=(lock_rect.centerx, wpm_rect.bottom + 20))
    screen.blit(instruction_surface, instruction_rect)

# detect whether a user has clicked on any lock and return the appropriate lock object
def detect_click(client, event):
    mouse_x, mouse_y = event.pos
    
    for lock in client.get_all_locks():
        row = lock.lock_id // GRID_ROWS
        col = lock.lock_id % GRID_COLS
       
        x = (col * CELL_SIZE) + PADDING
        y = (row * CELL_SIZE) + HUD_HEIGHT + HUD_VERT_OFFSET + GRID_ROW_OFFSET + 35  # +35 for stats bar

        if x <= mouse_x < x + CELL_SIZE and y <= mouse_y < y + CELL_SIZE:
            if not lock.broken:
                return lock
    
    return None

# Improved input handling to prevent key holding issues
def handle_typing_input(event, user_string, wpm_calculator=None):
    global key_states
    
    if event.type == pygame.KEYDOWN:
        key = event.key
        
        # Handle ENTER immediately (don't track it)
        if key == pygame.K_RETURN:
            return user_string, "SUBMIT"
        
        # Track other key presses
        if key not in key_states:
            key_states[key] = True
            
            if key == pygame.K_BACKSPACE:
                return user_string[:-1], "CONTINUE"
            elif event.unicode.isprintable():
                # Record keystroke for WPM calculation
                if wpm_calculator:
                    wpm_calculator.record_keystroke(event.unicode)
                return user_string + event.unicode, "CONTINUE"
    
    elif event.type == pygame.KEYUP:
        key = event.key
        # Don't track ENTER release
        if key != pygame.K_RETURN and key in key_states:
            del key_states[key]
    
    return user_string, "CONTINUE"

# start new game
def start_game():
    # temporary simulation of a server
    client = LocalGameClient(GRID_ROWS, GRID_COLS, user_id, icon)
    network.set_sim_grid(client.grid)
    network.set_sim_players(client.players)

    start_time = pygame.time.get_ticks()
    remaining_time = GAME_TIME
    total_points = 0
    total_locks = size
    remaining_locks = size

    user_string = ""
    current_wpm = None
    wpm_calculator = WPMCalculator()
    
    # while game timer has not finished
    while remaining_time != 0 :
        if remaining_locks == 0:
            return False
        
        # HUD information
        screen.fill(colors['backdrop'])
        remaining_time = countdown_timer(start_ticks=start_time, total_seconds=GAME_TIME)

        render(game=game, left_text="", right_text="", center_text="", start_time=start_time, 
               total_points=total_points, remaining_locks=remaining_locks, total_locks=total_locks, 
               remaining_time=remaining_time, current_wpm=current_wpm)

        # main input call loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
           # tracking keyboard inputs for lock screen
            if showing_lock_screen:
                user_string, action = handle_typing_input(event, user_string, wpm_calculator)
                
                if action == "SUBMIT":
                    # Calculate actual WPM
                    user_wpm = wpm_calculator.finish_typing()
                    current_wpm = user_wpm

                    # unlock attempt handling
                    success, points = game.break_lock(lock=lock, user_string=user_string, user_wpm=user_wpm)
                    
                    print(f"Lock break attempt: success={success}, points={points}, user_wpm={user_wpm}")
                    
                    if success:
                        remaining_locks -= 1
                        total_points += points
                        print(f"Lock broken! New total points: {total_points}")
                    
                    # reset lock and lock break screen for next attempt
                    lock = None
                    showing_lock_screen = False
                    user_string = ""
                    current_wpm = None
                    wpm_calculator.reset()

            else:
                # lock mouse click event
                if event.type == pygame.MOUSEBUTTONDOWN:
                    clicked = detect_click(client, event)
                    
                    # claim lock handling
                    if lock and lock.available and game.claim_lock(user=user_id, lock=lock):
                        lock_screen_start = pygame.time.get_ticks() 
                        user_string = ""
                        showing_lock_screen = True 
                        current_wpm = None
                        wpm_calculator.start_typing()
        
        # lock break rendering call with user typed input
        if showing_lock_screen:
            if (pygame.time.get_ticks() - lock_screen_start) // 1000 < 10:
                render_lock_screen(lock, user_string)                       
            
            # stop rendering next iteration
            else:
                submit_response = True
            
            if submit_response:
                dummy_wpm = 50
                network.send_break(lock.lock_id, user_input, dummy_wpm)                     # communicate with server to validate lock break
                waiting_for_break_result = True
                
                if waiting_for_break_result:
                    result = network.get_packet(MSG_BREAK_REQ)
                
                    if result:
                        client.grid.update_lock(Lock.from_dict(result.get("lock")))         # update game state based on server response (implicit update, agnostic of whether break was successful)
                        waiting_for_break_result = False
                
                showing_lock_screen = False
                submit_response = False
                user_input = ""
                lock = None
                current_wpm = None
                wpm_calculator.reset()
        
        # game UI update call
        pygame.display.flip()
        clock.tick(60)

    return False

# main loop to run the application itself
# main menu can be implemented here
running = True
while running:
    running = start_game()

network.close()
pygame.quit()
