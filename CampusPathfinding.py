import pygame
import numpy as np
import random
import speech_recognition as sr
import time
import os

# Initialize Pygame
pygame.init()

# Constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WINDOW_SIZE = (800, 600)
STEP_SIZE = 10
MAX_ITERATIONS = 5000

# Initialize the screen
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Interactive Pathfinding")

class Environment:
    def __init__(self, colour, x, y, width, height):
        self.colour = colour
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def create(self, screen):
        pygame.draw.rect(screen, self.colour, [self.x, self.y, self.width, self.height])

def point_in_triangle(point, triangle):
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    
    d1 = sign(point, triangle[0], triangle[1])
    d2 = sign(point, triangle[1], triangle[2])
    d3 = sign(point, triangle[2], triangle[0])

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

    return not (has_neg and has_pos)

def setup_environment():
    screen.fill(WHITE)
    building_centers = {}
    obstacles = []

    # Define buildings
    buildings = [
        Environment(BLACK, 50, 50, 100, 100),   # B1 - Main Hall
        Environment(BLACK, 50, 250, 100, 100),  # B2 - Library
        Environment(BLACK, 50, 450, 100, 100),  # B3 - Gym
        Environment(BLACK, 650, 50, 100, 100),  # B4 - Cafeteria
        Environment(BLACK, 650, 250, 100, 100), # B5 - Auditorium
        Environment(BLACK, 650, 450, 100, 100)  # B6 - Administrative Office
    ]

    labels = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6']
    names = ['Main Hall', 'Library', 'Gym', 'Cafeteria', 'Auditorium', 'Administrative Office']

    for i, building in enumerate(buildings):
        building.create(screen)
        obstacles.append(building)
        label = labels[i]
        name = names[i]
        font = pygame.font.Font(None, 36)
        text = font.render(label, True, WHITE)
        text_rect = text.get_rect(center=(building.x + building.width // 2, building.y + building.height // 2))
        screen.blit(text, text_rect)
        
        font_new = pygame.font.Font(None, 20)
        text_new = font_new.render(name, True, BLACK)
        text_rect_new = text_new.get_rect(center=(building.x + building.width // 2, building.y - 15))
        screen.blit(text_new, text_rect_new)
        
        if i < 3:  # Left side buildings
            building_centers[name.lower()] = (building.x + building.width + 10, building.y + building.height // 2)
        else:  # Right side buildings
            building_centers[name.lower()] = (building.x - 10, building.y + building.height // 2)

    # Define circular points
    circular_points = [
        (250, 150, 40, 'C1', 'Garden'),
        (250, 450, 40, 'C2', 'Library Courtyard'),
        (550, 150, 40, 'C3', 'Park'),
        (550, 450, 40, 'C4', 'Fountain')
    ]

    for x, y, r, label, name in circular_points:
        pygame.draw.circle(screen, BLACK, (x, y), r)
        obstacles.append(('circle', x, y, r))  # Store circular obstacles with type identifier
        font = pygame.font.Font(None, 24)
        text = font.render(label, True, WHITE)
        text_rect = text.get_rect(center=(x, y))
        screen.blit(text, text_rect)
        
        font_new = pygame.font.Font(None, 20)
        text_new = font_new.render(name, True, BLACK)
        text_rect_new = text_new.get_rect(center=(x, y - r - 15))
        screen.blit(text_new, text_rect_new)
        
        building_centers[name.lower()] = (x, y)

    # Define triangles
    triangles = [
        ([(350, 50), (400, 100), (450, 50)], 'T1', 'Canteen'),
        ([(350, 250), (400, 300), (450, 250)], 'T2', 'Fees Dept'),
        ([(350, 450), (400, 500), (450, 450)], 'T3', 'CSE'),
        ([(200, 300), (250, 350), (300, 300)], 'T4', '1st year'),
        ([(500, 300), (550, 350), (600, 300)], 'T5', '2nd year')
    ]

    for triangle, label, name in triangles:
        pygame.draw.polygon(screen, BLACK, triangle)
        obstacles.append(('triangle', triangle))  # Store triangular obstacles with type identifier
        font = pygame.font.Font(None, 20)
        text = font.render(label, True, WHITE)
        text_rect = text.get_rect(center=(sum(x for x, _ in triangle) // 3, sum(y for _, y in triangle) // 3))
        screen.blit(text, text_rect)
        
        font_new = pygame.font.Font(None, 16)
        text_new = font_new.render(name, True, BLACK)
        text_rect_new = text_new.get_rect(center=(sum(x for x, _ in triangle) // 3, min(y for _, y in triangle) - 10))
        screen.blit(text_new, text_rect_new)
        
        triangle_center = (sum(x for x, _ in triangle) // 3, sum(y for _, y in triangle) // 3)
        building_centers[name.lower()] = triangle_center

    pygame.display.flip()
    return building_centers, obstacles

def is_valid_point(x, y, obstacles):
    if not (0 <= x < WINDOW_SIZE[0] and 0 <= y < WINDOW_SIZE[1]):
        return False
    for obs in obstacles:
        if isinstance(obs, Environment):
            if obs.x <= x < obs.x + obs.width and obs.y <= y < obs.y + obs.height:
                return False
        elif isinstance(obs, tuple):
            if obs[0] == 'circle':
                _, cx, cy, r = obs
                if ((x - cx) ** 2 + (y - cy) ** 2) <= r ** 2:
                    return False
            elif obs[0] == 'triangle':
                _, triangle = obs
                if point_in_triangle((x, y), triangle):
                    return False
    return True

def RRT(start, goal, obstacles, max_iterations=MAX_ITERATIONS, step_size=STEP_SIZE):
    parent = {start: None}
    
    for _ in range(max_iterations):
        if random.random() < 0.1:
            x, y = goal
        else:
            x, y = random.randint(0, WINDOW_SIZE[0] - 1), random.randint(0, WINDOW_SIZE[1] - 1)
        
        if not is_valid_point(x, y, obstacles):
            continue
        
        nearest = min(parent.keys(), key=lambda p: ((p[0] - x) ** 2 + (p[1] - y) ** 2) ** 0.5)
        theta = np.arctan2(y - nearest[1], x - nearest[0])
        
        new_x = int(nearest[0] + step_size * np.cos(theta))
        new_y = int(nearest[1] + step_size * np.sin(theta))
        
        if is_valid_point(new_x, new_y, obstacles):
            new_point = (new_x, new_y)
            parent[new_point] = nearest
            pygame.draw.line(screen, BLUE, nearest, new_point, 1)
            pygame.display.update()
            
            if ((new_x - goal[0]) ** 2 + (new_y - goal[1]) ** 2) ** 0.5 < step_size:
                parent[goal] = new_point
                return parent
    
    return None

def backtrack_path(parent, start, goal):
    path = [goal]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path.reverse()
    return path

def get_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Please say your destination...")
        audio = recognizer.listen(source)
    
    try:
        destination = recognizer.recognize_google(audio).lower()
        print(f"You said: {destination}")
        return destination
    except sr.UnknownValueError:
        print("Sorry, I didn't understand that.")
        return None
    except sr.RequestError:
        print("Sorry, there was an error with the speech recognition service.")
        return None

def get_typed_input():
    font = pygame.font.Font(None, 32)
    input_box = pygame.Rect(300, 550, 200, 32)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        screen.fill((255, 255, 255), input_box)
        txt_surface = font.render(text, True, color)
        width = max(200, txt_surface.get_width()+10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.draw.rect(screen, color, input_box, 2)

        pygame.display.flip()

    return text.lower()

def main():
    # Set up the environment first
    building_centers, obstacles = setup_environment()
    
    # Set a fixed start point
    start = (30, 30)
    pygame.draw.circle(screen, RED, start, 5)
    pygame.display.flip()
    
    # Get input method from environment variable
    input_method = os.environ.get('INPUT_METHOD', 'type')
    
    if input_method == "voice":
        print("Please say your destination.")
        destination = get_voice_input()
    elif input_method == "type":
        print("Please type your destination.")
        destination = get_typed_input()
    else:
        print("Invalid input method. Exiting.")
        return

    if destination in building_centers:
        end = building_centers[destination]
        print(f"Calculating path to {destination}")
        
        parent = RRT(start, end, obstacles)
        
        if parent:
            path = backtrack_path(parent, start, end)
            
            # Draw final path
            for i in range(len(path) - 1):
                pygame.draw.line(screen, YELLOW, path[i], path[i+1], 4)
                pygame.display.update()
                time.sleep(0.01)
            
            # Draw start and end points
            pygame.draw.circle(screen, RED, start, 5)
            pygame.draw.circle(screen, GREEN, end, 5)
            
            pygame.display.flip()
        else:
            print("No path found")
    else:
        print("Destination not recognized.")
    
    # Keep the window open until user closes it
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    
    pygame.quit()

if __name__ == "__main__":
    main()