from glob import glob
import pygame
import time
import random
import sqlite3

red = (255, 0, 0)
green = (0, 255, 0)
black = (0, 0, 0)
purple = (128, 0, 128)
white = (255, 255, 255)
grey = (128, 128, 128)

width = 800
height = 800

pygame.init()
display = pygame.display.set_mode((width, height))
pygame.display.set_caption('Змейка')
font = pygame.font.SysFont("None", 35)
clock = pygame.time.Clock()

game_started = False
cursor_state = False

input_rect = pygame.Rect(width // 2 - 150, height // 4 - 50, 300, 100)
start_btn = pygame.Rect(width // 2 - 100, height // 2 - 50, 200, 100)

nick_name = ''

string_parts = []

string_parts.append([
    ["GGGGG", "G", "G     GG", "G        G", "G        G", "GGGGG"],
    ["   aaa", "         a", "   aaaa", "a        a", "a        a", "   aaa  a"],
    ["m  m  m", "mm  m  m", "mm  m  m", "mm  m  m", "mm  m  m"],
    ["  eee  ", "e      e", "eeeee", "e", "  eeee"]])

string_parts.append([
    ["  ooo  ", "o      o", "o      o", "o      o", "  ooo  "],
    ["v      v", "v      v", "v      v", "  v  v  ", "    v    "],
    ["  eee  ", "e      e", "eeeee", "e", "  eeee"],
    ["r  rrr", "rr      r", "r", "r", "r"]])

scores = []

db = sqlite3.connect('snake.db')
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS scores (
    nickname TEXT,
    score INT,
    speed INT
)""")
db.commit()

def load_scores():
    global scores
    global cursor

    cursor.execute(f"SELECT * FROM scores")
    scores = cursor.fetchall()


def save_score(nickname, score, speed):
    global scores
    global db
    global cursor

    cursor.execute(f"SELECT * FROM scores WHERE nickname = '{nickname}' AND speed = {speed}")
    result = cursor.fetchone()
    if result is None:
        cursor.execute(f"INSERT INTO scores VALUES (?, ?, ?)", (nickname, score, speed))
    elif result[2] == speed and result[1] < score:
        cursor.execute(f"UPDATE scores SET score WHERE nickname = '{nickname}' AND speed = {speed}")
    elif result[2] != speed:
        cursor.execute(f"INSERT INTO scores VALUES (?, ?, ?)", (nickname, score, speed))
    db.commit()


def check_nick(nick):
    if len(nick) == 0:
        return False
    else:
        return True


def show_game_over():
    global string_parts

    str_count = 0
    latter_size = 20
    str_x, str_y = 70, 50

    for latter in string_parts[0]:
        for string in latter:
            display.blit(font.render(string, True, red),
                         [str_x, str_y + str_count * latter_size])
            str_count += 1
        str_count += 1
    str_count = 10
    str_x = 200
    for latter in string_parts[1]:
        for string in latter:
            display.blit(font.render(string, True, red),
                         [str_x, str_y + str_count * latter_size])
            str_count += 1
        str_count += 1


def show_menu():
    pygame.draw.rect(
        display, purple, start_btn)

    display.blit(font.render("Go", True, white),
                 [width // 2 - 20, height // 2 - 10])

    pygame.draw.rect(
        display, white, input_rect)

    display.blit(font.render(nick_name, True, black),
                 [input_rect.x+5, input_rect.y+5])


def add_score_to_list(nick_name, score, speed):
    global scores
    nick_exists = False
    for i in range(len(scores)):
        if scores[i][0] == nick_name and speed == scores[i][2]:
            nick_exists = True
            if scores[i][1] < score:
                scores[i] = (nick_name, score, speed)
            break
    if not nick_exists:
        scores.append((nick_name, score, speed))
    

def sort_scores(speed):
    global scores
    global cursor
    cursor.execute(f"SELECT nickname, score FROM scores WHERE speed = {speed} ORDER BY score DESC")
    sorted_scores = cursor.fetchmany(10)

    return sorted_scores
    

def print_score_list(scores_for_print, speed):
    step = 20
    c_pos = 0
    display.fill(green)

    display.blit(font.render(f'Топ {len(scores_for_print)} со скоростью {speed}:', True, black), [width // 2, 200 + c_pos])
    c_pos += step

    for i in range(len(scores_for_print)):
        display.blit(font.render(str(i+1) + ") " + scores_for_print[i][0] + ": " + str(scores_for_print[i][1]), True, black),
                     [width // 2, 200 + c_pos])
        c_pos += step


def show_score_list(scores_for_print, speed):
    events = pygame.event.get()
    for e in events:
        if e.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif e.type == pygame.KEYDOWN:
            return

    print_score_list(scores_for_print, speed)
    pygame.display.flip()


class Game:
    segment_size = 0
    speed = 0

    head_x = 0
    head_y = 0

    snake_length = 0
    snake = []

    vx = 0
    vy = 0

    def __init__(self):
        self.segment_size = 20
        self.speed = 10

        self.head_x = width // 2 // self.segment_size * self.segment_size
        self.head_y = height // 2 // self.segment_size * self.segment_size

        self.snake_length = 1
        self.snake = []

        self.vx = 0
        self.vy = 0

        self.fruit_x, self.fruit_y = self.get_random_point()

    def get_random_point(self):
        x = random.randint(
            0, width - self.segment_size) // self.segment_size * self.segment_size
        y = random.randint(
            0, height - self.segment_size) // self.segment_size * self.segment_size
        return (x, y)

    def show_snake(self, snake):
        for segment in snake:
            pygame.draw.rect(display, black, [
                             segment[0], segment[1], self.segment_size, self.segment_size])

    def show_score(self, score):
        display.blit(font.render('Счёт: ' + str(score), True, black), [0, 0])
        display.blit(font.render("Скорость: " +
                     str(self.speed), True, black), [600, 0])

    def is_eat_self(self, snake, head_x, head_y):
        for i in range(len(snake) - 1):
            if snake[i][0] == head_x and snake[i][1] == head_y:
                return True
        return False

    def Play(self, display, font, clock):
        global nick_name
        while True:
            if (
                self.head_x < 0
                or self.head_x >= width
                or self.head_y < 0
                or self.head_y >= height
                or self.is_eat_self(self.snake, self.head_x, self.head_y)
            ):
                add_score_to_list(nick_name, self.snake_length - 1, self.speed)
                save_score(nick_name, self.snake_length - 1, self.speed)
                scores_for_print = sort_scores(self.speed)

                show_score_list(scores_for_print, self.speed)
                show_game_over()

                pygame.display.flip()

                while True:
                    events = pygame.event.get()
                    for e in events:
                        if e.type == pygame.QUIT:
                            save_score(nick_name, self.snake_length - 1, self.speed)
                            pygame.quit()
                            quit()
                        elif e.type == pygame.KEYDOWN:
                            return

            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    save_score(nick_name, self.snake_length - 1, self.speed)
                    pygame.quit()
                    quit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_s and (self.vy != -self.segment_size or self.snake_length == 1):
                        self.vx = 0
                        self.vy = self.segment_size
                    if e.key == pygame.K_w and (self.vy != self.segment_size or self.snake_length == 1):
                        self.vx = 0
                        self.vy = -self.segment_size
                    if e.key == pygame.K_a and (self.vx != self.segment_size or self.snake_length == 1):
                        self.vx = -self.segment_size
                        self.vy = 0
                    if e.key == pygame.K_d and (self.vx != -self.segment_size or self.snake_length == 1):
                        self.vx = self.segment_size
                        self.vy = 0
                    if e.key == pygame.K_DOWN:
                        if self.speed > 1:
                            self.speed -= 1
                    if e.key == pygame.K_UP:
                        if self.speed < 30:
                            self.speed += 1

            self.head_x += self.vx
            self.head_y += self.vy

            display.fill(green)

            pygame.draw.rect(
                display, red, [self.fruit_x, self.fruit_y, self.segment_size, self.segment_size])
            pygame.draw.rect(display, black, [
                self.head_x, self.head_y, self.segment_size, self.segment_size])
            self.snake.append((self.head_x, self.head_y))

            if len(self.snake) > self.snake_length:
                del self.snake[0]

            self.show_snake(self.snake)
            self.show_score(self.snake_length - 1)

            if self.head_x == self.fruit_x and self.head_y == self.fruit_y:
                self.fruit_x, self.fruit_y = self.get_random_point()
                self.snake_length += 1

            pygame.display.flip()
            clock.tick(self.speed)

load_scores()

while True:
    if not game_started:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit()
                quit()
            if e.type == pygame.MOUSEBUTTONUP:
                if e.button == 1:  # 1 - left 2 - right 3 - wheel
                    pos = pygame.mouse.get_pos()  # [x, y]
                    if (pos[0] >= width // 2 - 100
                        and pos[0] <= width // 2 + 100
                        and pos[1] >= height // 2 - 50
                        and pos[1] <= height // 2 + 50
                            and check_nick(nick_name)):
                        game_started = True
                        cursor_state = False
                    elif (pos[0] >= width // 2 - 150
                          and pos[0] <= width // 2 + 150
                          and pos[1] >= height // 4 - 50
                          and pos[1] <= height // 4 + 50):
                        cursor_state = True
                    else:
                        cursorState = False
            if e.type == pygame.KEYUP and cursor_state:
                if e.key == pygame.K_BACKSPACE:
                    nick_name = nick_name[:-1]
                else:
                    if (len(nick_name) < 15):
                        nick_name += e.unicode

        display.fill(green)

        show_menu()

        pygame.display.flip()

    else:
        g = Game()
        g.Play(display, font, clock)
        game_started = False
