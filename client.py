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
hud_font = pygame.font.SysFont(None, 22)

# client side networking handler
network = ClientNetwork(user_id)

# helper to render the scoreboard text with current data
def render_hud_text(hud_rect, player_dict):
    x = hud_rect.left + 10
    y = hud_rect.top + 5
    spacing = 5
    
    for player_id, pdata in player_dict.items():
        icon = pdata["icon"]
        score = pdata["score"]
        broken = pdata["locks_broken"]
        text = f"{icon} {player_id} | Points: {score} | Locks: {broken}"
        
        surface = hud_font.render(text, True, colors["hud_text"])
        screen.blit(surface, (x, y))
        y += surface.get_height() + spacing

# renders the main game layout
def render_grid(client, start_time):
    current_time = pygame.time.get_ticks()
    hud_rect = pygame.Rect(HUD_PADDING, HUD_VERT_OFFSET, SCREEN_WIDTH - (2 * HUD_PADDING), HUD_HEIGHT * 2)
    
    pygame.draw.rect(screen, colors["hud_backdrop"], hud_rect)
    render_hud_text(hud_rect, client.get_player_dict())
    
    # draws all locks
    for lock in client.get_all_locks():
        row = lock.lock_id // GRID_ROWS
        col = lock.lock_id % GRID_COLS
       
        x = (col * CELL_SIZE) + PADDING
        y = (row * CELL_SIZE) + HUD_HEIGHT * 2 + HUD_VERT_OFFSET + GRID_ROW_OFFSET
        cell = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        
        pygame.draw.rect(screen, colors[lock.difficulty], cell)
        pygame.draw.rect(screen, colors["border"], cell, width=BORDER_WIDTH)
        
        # draw player icon if the lock is claimed
        # draw "lock broken" icon if lock is broken
        icon = ""
        if lock.claimed_by_user:
            icon = client.get_player_dict().get(lock.claimed_by_user, {}).get("icon", "")
        
        elif lock.broken:
            icon = "▢"
        
        # default, just renders empty string on top of locks
        if icon:
            text_surface = font.render(icon, True, colors["lock_text"])                         
            screen.blit(text_surface, text_surface.get_rect(center=cell.center))
        
        # displays the points of each lock briefly at the start of the gamefades the points text by changing opacity
        else:
            fade_duration = 2000
            elapsed_time = current_time - start_time
            
            if elapsed_time < fade_duration:
                alpha = 255 - int((elapsed_time / fade_duration) * 255)
                text_surface = font.render(str(lock.points), True, colors["lock_text"])
                text_surface.set_alpha(max(0, alpha))
                text_surface = text_surface.convert_alpha()
                screen.blit(text_surface, text_surface.get_rect(center=cell.center))

# helper to render the typing screen after clicking a lock
def render_lock_screen(lock, user_input):
    padding = 30
    text_gap = 40
    lock_rect = pygame.Rect(padding, SCREEN_HEIGHT // 4, SCREEN_WIDTH - 2 * padding, SCREEN_HEIGHT // 2)
    
    pygame.draw.rect(screen, colors["hud_backdrop"], lock_rect)
    
    wrapped_text = wrap_text(lock.lock_string, font, lock_rect.width - 2 * padding)
    y = lock_rect.top + 30
    
    for line in wrapped_text:
        rendered = font.render(line, True, colors["hud_text"])
        screen.blit(rendered, (lock_rect.centerx - rendered.get_width() // 2, y))
        
        y += rendered.get_height() + 5
    
    typed_surface = font.render(user_input, True, colors["hud_text"])
    screen.blit(typed_surface, typed_surface.get_rect(midtop=(lock_rect.centerx, y + text_gap)))

# helper to fit text inside given box space (does not work perfectly)
def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines

# detect whether a user has clicked on any lock and return the appropriate lock object
def detect_click(client, event):
    mouse_x, mouse_y = event.pos
    
    for lock in client.get_all_locks():
        row = lock.lock_id // GRID_ROWS
        col = lock.lock_id % GRID_COLS
       
        x = (col * CELL_SIZE) + PADDING
        y = (row * CELL_SIZE) + HUD_HEIGHT * 2 + HUD_VERT_OFFSET + GRID_ROW_OFFSET
        
        if x <= mouse_x < x + CELL_SIZE and y <= mouse_y < y + CELL_SIZE:
            if not lock.broken:
                return lock
    
    return None

# main game state management
def start_game():
    # temporary simulation of a server
    client = LocalGameClient(GRID_ROWS, GRID_COLS, user_id, icon)
    network.set_sim_grid(client.grid)
    network.set_sim_players(client.players)

    start_time = pygame.time.get_ticks()
    remaining_time = GAME_TIME                                                              # time left in game
    lock = None
    user_input = ""
    showing_lock_screen = False
    submit_response = False

    while remaining_time > 0:
        # fetch grid updates and player info dict
        game_update_pkt = network.get_packet(MSG_GRID_UPDATE)
        if game_update_pkt:
            client.grid = Grid.from_dict(game_update_pkt.get("grid"), GRID_ROWS, GRID_COLS)
            client.players = game_update_pkt.get("players")
            
        screen.fill(colors['backdrop'])
        remaining_time = countdown_timer(start_time, GAME_TIME)        
        render_grid(client, start_time)                                                    # main rendering call

        # main input call loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
           # tracking keyboard inputs for lock screen
            if showing_lock_screen:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:                                        # when user presses enter in lock break screen to submit input
                        submit_response = True
                    
                    # update user input after backspace
                    elif event.key == pygame.K_BACKSPACE:   
                        user_input = user_input[:-1]

                    # update user input if key press
                    elif event.unicode.isprintable():
                        user_input += event.unicode
                        
            else:       
                if event.type == pygame.MOUSEBUTTONDOWN:
                    clicked = detect_click(client, event)
                    
                    # main lock claim sequence
                    if clicked is not None:
                        network.send_claim(clicked.lock_id)                                 # communicate with server to validate lock claim
                        result = network.get_packet(MSG_CLAIM_REQ)
                        
                        if result:
                            client.grid.update_lock(Lock.from_dict(result.get("lock")))     # update game state based on server response (implicit update, agnostic of whether claim was successful)
                        
                        # display lock screen in next iteration
                        lock = clicked                                                      # lock object that the player is currently working on
                        user_input = ""
                        showing_lock_screen = True
                        lock_screen_start = pygame.time.get_ticks()

        # main lock break sequence
        if showing_lock_screen:
            if (pygame.time.get_ticks() - lock_screen_start) // 1000 < 10:                  # give user a maximum of 10 seconds
                render_lock_screen(lock, user_input)
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

        # refresh the screen, capped to 60 fps (artificially slows tick cycle to accommodate for networking delays)
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
