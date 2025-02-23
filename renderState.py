import pygame
import sys
import time
from levelParser import parse_level_file
import ast
import numpy as np
import os

def render_state(level_path='levels/MAPF00.lvl', state=[], output_path="rendered_state"):
    # Initialize Pygame
    pygame.init()

    level_meta_data = parse_level_file(level_path)
    level_state = state.__repr__().split('\n')

    # Define maximum window size
    MAX_WINDOW_WIDTH = 900
    MAX_WINDOW_HEIGHT = 600

    # Get width and height of the level
    GRID_WIDTH = len(level_state[0])
    GRID_HEIGHT = len(level_state)

    # Calculate the tile size based on the level dimensions and maximum window size
    TILE_SIZE = min(MAX_WINDOW_WIDTH // GRID_WIDTH, MAX_WINDOW_HEIGHT // GRID_HEIGHT)

    # Calculate the window dimensions based on the tile size
    WINDOW_WIDTH = TILE_SIZE * GRID_WIDTH
    WINDOW_HEIGHT = TILE_SIZE * GRID_HEIGHT - TILE_SIZE  # Subtract one tile size to make room for metadata box

    # Define colors
    BACKGROUND_COLOR = (224, 224, 224)
    WALL_COLOR = (0, 0, 0)
    PLAYER_COLOR = (0, 162, 255)
    BOX_COLOR = (0, 162, 255)
    GOAL_COLOR = (251, 232, 144)
    OUTLINE_COLOR = (0, 0, 0)
    TEXT_COLOR = (255, 255, 255)

    # Level definition symbols
    agent_symbols = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    box_symbols = [chr(i).lower() for i in range(65, 91)]
    level_data = level_state

    # Metadata box height
    META_BOX_HEIGHT = TILE_SIZE

    # Initialize off-screen surface
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT + META_BOX_HEIGHT))

    # Game state initialization
    agent_positions = []
    boxes = []  # Changed from set to list to maintain order
    walls = set()

    # Functions to find goals
    def find_agent_goals(goal_description):
        cells = len(goal_description[0]) * len(goal_description)
        possible_goals = str(np.arange(cells))
        goals_dict = {}
        for x, row in enumerate(goal_description):
            for y, cell in enumerate(row):
                if cell != ' ' and cell in possible_goals:
                    goals_dict[cell] = (y, x)
        return goals_dict

    def find_box_goals(goal_description):
        cells = len(goal_description[0]) * len(goal_description)
        possible_goals = [chr(i).lower() for i in range(65, 91)][:cells]
        goals_dict = {}
        for x, row in enumerate(goal_description):
            for y, cell in enumerate(row):
                if cell != ' ' and cell.lower() in possible_goals:
                    if cell not in goals_dict:
                        goals_dict[cell] = []
                    goals_dict[cell].append((y, x))
        return goals_dict

    goals_dict = find_agent_goals(level_meta_data['#goal'])
    goals = set(goals_dict.values())
    box_goal_dict = find_box_goals(level_meta_data['#goal'])

    # Flatten the dictionary into a list of tuples with positions and labels
    box_goals = []
    for label, positions in box_goal_dict.items():
        for pos in positions:
            box_goals.append((pos, label, True))

    # Parse agents from the level map and ensure they are sorted by their ID
    for y, row in enumerate(level_data):
        for x, tile in enumerate(row):
            if tile == '+':
                walls.add((x, y))
            elif tile in agent_symbols:
                agent_positions.append((int(tile), (x, y)))
            elif tile.lower() in box_symbols:
                boxes.append(((x, y), tile))  # Store as tuples of (position, label)

    # Sort agents by their numerical ID
    agent_positions.sort(key=lambda agent: agent[0])

    # Extract only positions for further processing (order now matches sorted IDs)
    agent_positions = [pos for _, pos in agent_positions]

    # Function to draw text
    def draw_text(surface, text, pos, color=(255, 255, 255)):
        font = pygame.font.SysFont("Arial", 42, bold=True)
        text_render = font.render(text, True, color)
        surface.blit(text_render, pos)

    # Function to draw metadata box
    def draw_metadata_box(surface, level_name, search_strategy='bfs', num_generated=0, sol_length=0, time_elapsed=0):
        pygame.draw.rect(surface, WALL_COLOR, (0, 0, WINDOW_WIDTH, META_BOX_HEIGHT))
        font = pygame.font.SysFont("Helvetica", 14, bold=False)
        line1 = f"Level: {level_name}  |  Search Strategy: {search_strategy}"
        line2 = f"States Generated: {num_generated} | Solution Length: {sol_length} | Time: {time_elapsed}"
        line1_surface = font.render(line1, True, TEXT_COLOR)
        line2_surface = font.render(line2, True, TEXT_COLOR)
        line1_rect = line1_surface.get_rect(center=(WINDOW_WIDTH // 2, META_BOX_HEIGHT*1.5 // 4))
        line2_rect = line2_surface.get_rect(center=(WINDOW_WIDTH // 2, 3 * META_BOX_HEIGHT // 4))
        surface.blit(line1_surface, line1_rect)
        surface.blit(line2_surface, line2_rect)

    # Function to draw grid lines
    def draw_grid_lines():
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(surface, WALL_COLOR, (x * TILE_SIZE, META_BOX_HEIGHT), (x * TILE_SIZE, META_BOX_HEIGHT + WINDOW_HEIGHT))
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(surface, WALL_COLOR, (0, META_BOX_HEIGHT + y * TILE_SIZE), (WINDOW_WIDTH, META_BOX_HEIGHT + y * TILE_SIZE))

    # Function to draw the game state
    def draw():
        surface.fill(BACKGROUND_COLOR)
        draw_grid_lines()

        for wall in walls:
            pygame.draw.rect(surface, WALL_COLOR, (*[i * TILE_SIZE for i in wall], TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(surface, WALL_COLOR, (0, META_BOX_HEIGHT + WINDOW_HEIGHT - TILE_SIZE, WINDOW_WIDTH, TILE_SIZE))

        goal_size_fraction = 0.9
        goal_size = TILE_SIZE * goal_size_fraction
        goal_center_offset = (TILE_SIZE - goal_size) // 2

        for goal in goals:
            pygame.draw.circle(surface, GOAL_COLOR, (
                goal[0] * TILE_SIZE + TILE_SIZE // 2,
                goal[1] * TILE_SIZE + TILE_SIZE // 2
            ), goal_size // 2)
            pygame.draw.circle(surface, OUTLINE_COLOR, (
                goal[0] * TILE_SIZE + TILE_SIZE // 2,
                goal[1] * TILE_SIZE + TILE_SIZE // 2
            ), goal_size // 2, 1)
            font = pygame.font.SysFont("Arial", 32, bold=True)
            text_surface = font.render(str(list(goals_dict.keys())[list(goals_dict.values()).index(goal)]), True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=(goal[0] * TILE_SIZE + TILE_SIZE // 2, goal[1] * TILE_SIZE + TILE_SIZE // 2))
            surface.blit(text_surface, text_rect)

        for goal in box_goals:
            position, label, is_goal = goal
            x, y = position
            box_size_fraction = 0.8
            box_size = TILE_SIZE * box_size_fraction
            box_center_offset = (TILE_SIZE - box_size) // 2

            pygame.draw.rect(surface, GOAL_COLOR, (
                x * TILE_SIZE + box_center_offset,
                y * TILE_SIZE + box_center_offset,
                box_size,
                box_size
            ))
            pygame.draw.rect(surface, OUTLINE_COLOR, (
                x * TILE_SIZE + box_center_offset,
                y * TILE_SIZE + box_center_offset,
                box_size,
                box_size
            ), 1)
            font = pygame.font.SysFont("Arial", 32, bold=True)
            text_surface = font.render(label, True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2))
            surface.blit(text_surface, text_rect)

        player_radius = TILE_SIZE // 2 - 5
        outline_radius = player_radius + 1
        for idx, pos in enumerate(agent_positions):
            center_pos = (pos[0] * TILE_SIZE + TILE_SIZE // 2, pos[1] * TILE_SIZE + TILE_SIZE // 2)
            pygame.draw.circle(surface, OUTLINE_COLOR, center_pos, outline_radius)
            pygame.draw.circle(surface, PLAYER_COLOR, center_pos, player_radius)
            font = pygame.font.SysFont("Arial", 32, bold=True)
            text_surface = font.render(str(idx), True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=center_pos)
            surface.blit(text_surface, text_rect)

        draw_metadata_box(surface, level_name=level_meta_data['#levelname'])

    # Render the state to the surface
    draw()

    # Save the rendered state as an image
    pygame.image.save(surface, output_path+'.png')
    print(f"State rendered and saved to {output_path+'.png'}")
    pygame.quit()

# Example usage:
# render_state_to_image('levels/MAPF00.lvl', state, 'rendered_state.png')
