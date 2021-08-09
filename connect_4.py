from numpy.core.defchararray import title
import pygame
import numpy as np
from pygame.locals import *
from tkinter import *
from tkinter import messagebox
import socket
import pickle
import select

def update_board(screen, status, centers, radius, no_of_circles):
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    BLACK = (0, 0, 0)
    for i in range(no_of_circles):
        for j in range(no_of_circles):
            if status[i][j] == 1:
                circle_rect = pygame.draw.circle(screen, YELLOW, centers[i][j], radius, 0)
            elif status[i][j] == 2:
                circle_rect = pygame.draw.circle(screen, RED, centers[i][j], radius, 0)
            else:
                circle_rect = pygame.draw.circle(screen, BLACK, centers[i][j], radius, 0)
    pygame.display.update()

def get_centers(no_of_circles):
    centers = []
    padding = 10
    radius = 30
    dist_row = radius + padding
    for i in range(no_of_circles):
        row = []
        dist_col = radius + padding
        for j in range(no_of_circles):
            row.append((dist_col, dist_row))
            dist_col = dist_col + radius * 2 + padding
        centers.append(row)
        dist_row = dist_row + radius * 2 + padding
    return centers, radius, padding

def init_board(screen, status, no_of_circles, font):
    centers, radius, padding = get_centers(no_of_circles)
    update_board(screen, status, centers,radius, no_of_circles)
    player_rect = pygame.draw.rect(screen, (139, 69, 19), [0, 500, 500, 100])
    p1_text = font.render("Player 1", 1, (255, 215, 0))
    p2_text = font.render("Player 2", 1, (0, 0, 0))
    screen.blit(p1_text, (50, 520))
    screen.blit(p2_text, (275, 520))
    return centers, radius, padding

def check_won_condition(status, no_of_circles, player):
    for i in range(no_of_circles):
        for j in range(no_of_circles - 3):
            if status[i][j] == player and status[i][j + 1] == player and status[i][j + 2] == player and status[i][j + 3] == player:
                return True
    
    for i in range(no_of_circles - 3):
        for j in range(no_of_circles):
            if status[i][j] == player and status[i + 1][j] == player and status[i + 2][j] == player and status[i + 3][j] == player:
                return True

    for i in range(no_of_circles - 3):
        for j in range(no_of_circles - 3):
            if status[i][j] == player and status[i + 1][j + 1] == player and status[i + 2][j + 2] == player and status[i + 3][j + 3] == player:
                return True

    for i in range(no_of_circles - 3):
        for j in range(3, no_of_circles):
            if status[i][j] == player and status[i + 1][j - 1] == player and status[i + 2][j - 2] == player and status[i + 3][j - 3] == player:
                return True
    
    return False

def add_circle(screen, event, status, centers, no_of_circles, playing, radius, padding, font, game_over, socket_status, socket):
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    player_1 = 1
    player_2 = 2
    col = event.pos[0] // (radius * 2 + padding)
    for i in range(no_of_circles - 1, -1, -1):
        if status[i][col] == 0:
            if playing == player_1:
                status[i][col] = 1
                circle_rect = pygame.draw.circle(screen, YELLOW, centers[i][col], radius, 0)
                pygame.display.update(circle_rect)
                played = True
                if check_won_condition(status,no_of_circles, playing):
                    print("Player_", playing, " Wins!!")
                    win = font.render("Player 1 WINS!!", 0, (255, 215, 0), (0, 0, 0))
                    screen.blit(win, (100, 250))
                    pygame.display.update()
                    Tk().wm_withdraw()
                    reply = messagebox.askquestion("askquestion", "Player 1 wins \n Play Again?")
                    if reply == 'yes':
                        new_game(screen, socket_status)
                    else:
                        game_over = True
                break
            elif playing == player_2:
                status[i][col] = 2
                circle_rect = pygame.draw.circle(screen, RED, centers[i][col], radius, 0)
                pygame.display.update(circle_rect)
                played = True
                if check_won_condition(status,no_of_circles, playing):
                    print("Player_", playing, " Wins!!")
                    win = font.render("Player 2 WINS!!", 0, (255, 215, 0), (0, 0, 0))
                    screen.blit(win, (100, 250))
                    pygame.display.update()
                    Tk().wm_withdraw()
                    reply = messagebox.askquestion("askquestion", "Player 2 wins \n Play Again?")
                    if reply == 'yes':
                        new_game(screen, socket_status)
                    else:
                        game_over = True
                break
    data = {"Status" : status, "Playing" : playing}
    socket.send(pickle.dumps(data))
    return status, game_over, played

def new_game(screen, socket_status):
    pygame.font.init()    
    no_of_circles = 7
    player_1 = 1
    player_2 = 2
    playing = player_1
    played = False
    status = np.zeros((no_of_circles, no_of_circles), dtype=int)
    font = pygame.font.SysFont('Comic Sans MS', 40)    
    pygame.display.set_caption("Connect 4")
    screen.fill((65, 105, 225))
    game_over = False
    centers, radius, padding = init_board(screen, status,no_of_circles, font)    
    if socket_status == "host":
        player_socket = host_game()
        game_socket, addr = player_socket.accept()
        game_socket.setblocking(0)
    elif socket_status == "join":
        game_socket = join_game()
    if socket_status == "host":
        SEND = 0
    else:
        SEND = 1
    while not game_over:
        if socket_status == "host" and SEND == 0:
            SEND = 1
        elif SEND == 1:
            ready = select.select([game_socket], [], [], 0.1)
            if ready[0]:
                data = game_socket.recv(4096)
                data = pickle.loads(data)
                status = data["Status"]
                playing = data["Playing"] 
                if playing == player_1:
                    playing = player_2
                else:
                    playing = player_1
                if playing == player_2:
                    # playing = player_2
                    p1_text = font.render("Player 1", 1, (0, 0, 0))
                    p2_text = font.render("Player 2", 1, (255, 0, 0))
                    screen.blit(p1_text, (50, 520))
                    screen.blit(p2_text, (275, 520))
                    played = False
                elif playing == player_1:
                    # playing = player_1
                    p1_text = font.render("Player 1", 1, (255, 215, 0))
                    p2_text = font.render("Player 2", 1, (0 , 0, 0))
                    screen.blit(p1_text, (50, 520))
                    screen.blit(p2_text, (275, 520))
                    played = False
                pygame.display.update()
                update_board(screen, status, centers,radius, no_of_circles)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if event.pos[0] % (radius * 2 + padding) > 10 and event.pos[1] < 500:
                    status, game_over, played = add_circle(screen, event, status, centers, no_of_circles, playing, radius, padding, font, game_over, socket_status, game_socket)                  
        pygame.display.update()
    return game_over

def menu_screen(screen):
    screen.fill((153, 255, 255))
    font = pygame.font.SysFont('Comic Sans MS', 40)
    title_font = pygame.font.SysFont('Comic Sans MS', 60)
    way_font = pygame.font.SysFont('Comic Sans MS', 20)
    host = font.render("Host", 1, (255, 255, 255))
    join = font.render("Join", 1, (255, 255, 255))    
    way = way_font.render("Select a way to play multiplayer", 1, (0, 0, 0))
    title = title_font.render("Connect 4", 1, (0, 0, 0))
    pygame.draw.rect(screen, (0, 0, 0), [60, 300, 150, 50])
    pygame.draw.rect(screen, (0, 0, 0), [290, 300, 150, 50])
    screen.blit(host, (85, 295))
    screen.blit(join, (315, 295))
    screen.blit(title, (100, 150))
    screen.blit(way, (90, 250))

def host_game():
    game_socket = socket.socket()
    port = 6555
    game_socket.bind(('', port))
    game_socket.listen(5)
    return game_socket

def join_game():
    game_socket = socket.socket()
    port = 6555
    game_socket.connect(('127.0.0.1', port))
    game_socket.setblocking(0)
    return game_socket

def connect():
    pygame.init()
    size = (500, 600)
    screen = pygame.display.set_mode(size)
    menu_screen(screen)
    game_status = False
    game_over = False
    while not game_status:
        if game_over:
            menu_screen(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if 60 <= event.pos[0] <= 210 and 300 <= event.pos[1] <= 350:
                    game_over = new_game(screen, "host")
                if 290 <= event.pos[0] <= 440 and 300 <= event.pos[1] <= 350:
                    game_over = new_game(screen, "join")
        pygame.display.update()

if __name__ == '__main__': connect()