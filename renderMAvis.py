import pygame
import sys
import time
import argparse
from levelParser import parse_level_file
import ast
import numpy as np

# Initialize Pygame
pygame.init()

# Argument parsing
parser = argparse.ArgumentParser(description="Process a string representation of a plan on a given level.")
parser.add_argument('--level', type=str, required=True, help='A path to a level file')
parser.add_argument('--plan', type=str, required=True, help='A string representation of a plan')
parser.add_argument('--search_strategy', type=str, required=False, default='bfs', help='The search strategy used to find the plan')
parser.add_argument('--num_generated', type=str, required=False, default=0, help='The number of states generated during the search')
parser.add_argument('--time_elapsed', type=str, required=False, default=0, help='The time elapsed during the search')
parser.add_argument('--sol_length', type=str, required=False, default=0, help='The length of the solution plan')
args = parser.parse_args()

# Convert plan string to action plan
def convert_str_to_plan(plan_str):
    try:
        action_plan = ast.literal_eval(plan_str)
    except (ValueError, SyntaxError):
        print("Invalid plan format. Please provide a valid list of agent actions.")
        sys.exit(1)
    return action_plan

action_plan = convert_str_to_plan(args.plan)
level_file = args.level

# Load level
level_meta_data = parse_level_file(level_file)

# Directions and direction map
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

direction_map = {
    "Move(N)": UP,
    "Move(S)": DOWN,
    "Move(E)": RIGHT,
    "Move(W)": LEFT,
    "NoOp": (0, 0)  # No operation
}

# Define maximum window size
MAX_WINDOW_WIDTH = 900
MAX_WINDOW_HEIGHT = 600

# Get width and height of the level
GRID_WIDTH = len(level_meta_data['#initial'][0])
GRID_HEIGHT = len(level_meta_data['#initial'])

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
level_data = level_meta_data['#initial']

# Metadata box height
META_BOX_HEIGHT = TILE_SIZE

# Initialize window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT + META_BOX_HEIGHT))
pygame.display.set_caption("MAvis Hospital")

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

# Function to interpolate positions
def interpolate_position(start, end, progress):
    """Linearly interpolate between two positions."""
    return (start[0] + (end[0] - start[0]) * progress,
            start[1] + (end[1] - start[1]) * progress)

# Function to move agents
def move_agents(actions):
    global agent_positions, boxes
    new_agent_positions = list(agent_positions)
    new_box_positions = list(boxes)

    for i, (action, pos) in enumerate(zip(actions, agent_positions)):
        if action.startswith("Move"):
            direction = direction_map.get(action, (0, 0))
            new_pos = (pos[0] + direction[0], pos[1] + direction[1])
            if new_pos not in walls and all(new_pos != box_pos for box_pos, _ in new_box_positions):
                new_agent_positions[i] = new_pos

        elif action.startswith("Push"):
            push_action, box_direction_str = action.replace('Push(', '').replace(')', '').split(',')
            push_direction = direction_map.get(f"Move({push_action})", (0, 0))
            box_direction = direction_map.get(f"Move({box_direction_str})", (0, 0))
            box_pos = (pos[0] + push_direction[0], pos[1] + push_direction[1])
            new_box_pos = (box_pos[0] + box_direction[0], box_pos[1] + box_direction[1])
            for index, (b_pos, label) in enumerate(new_box_positions):
                if b_pos == box_pos:
                    if new_box_pos not in walls and new_box_pos not in new_agent_positions and all(new_box_pos != other_b_pos for other_b_pos, _ in new_box_positions):
                        new_box_positions[index] = (new_box_pos, label)
                        new_agent_positions[i] = box_pos
                    break

        elif action.startswith("Pull"):
            pull_action, box_direction_str = action.replace('Pull(', '').replace(')', '').split(',')
            pull_direction = direction_map.get(f"Move({pull_action})", (0, 0))
            box_direction = direction_map.get(f"Move({box_direction_str})", (0, 0))
            box_pos = (pos[0] - box_direction[0], pos[1] - box_direction[1])
            agent_new_pos = (pos[0] + pull_direction[0], pos[1] + pull_direction[1])
            for index, (b_pos, label) in enumerate(new_box_positions):
                if b_pos == box_pos:
                    if agent_new_pos not in walls and agent_new_pos not in new_agent_positions and all(agent_new_pos != other_b_pos for other_b_pos, _ in new_box_positions):
                        new_box_positions[index] = (pos, label)
                        new_agent_positions[i] = agent_new_pos
                    break

    # Interpolation and animation
    sub_steps = 10
    for step in range(1, sub_steps + 1):
        progress = step / sub_steps
        interpolated_agents = [
            interpolate_position(old, new, progress) for old, new in zip(agent_positions, new_agent_positions)
        ]
        interpolated_boxes = [
            (interpolate_position(old[0], new[0], progress), old[1]) for old, new in zip(boxes, new_box_positions)
        ]
        draw(interpolated_agents, interpolated_boxes)
        pygame.time.wait(10)  # Control animation speed

    # Final position update
    agent_positions = new_agent_positions
    boxes = new_box_positions

# Function to draw text
def draw_text(surface, text, pos, color=(255, 255, 255)):
    font = pygame.font.SysFont("Arial", 42, bold=True)
    text_render = font.render(text, True, color)
    surface.blit(text_render, pos)

# Function to draw metadata box
def draw_metadata_box(screen, level_name, search_strategy='bfs', num_generated=0, sol_length=0, time_elapsed=0):
    """Draws a metadata box with given text above the Sokoban grid."""
    # Draw background for the metadata box
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, WINDOW_WIDTH, META_BOX_HEIGHT))
    
    # Define font
    font = pygame.font.SysFont("Helvetica", 14, bold=False)
    
    # Create text surfaces
    line1 = f"Level: {level_name}  |  Search Strategy: {search_strategy}"
    line2 = f"States Generated: {num_generated} | Solution Length: {sol_length} | Time: {time_elapsed}"
    
    # Render text lines
    line1_surface = font.render(line1, True, TEXT_COLOR)
    line2_surface = font.render(line2, True, TEXT_COLOR)
    
    # Position the text lines
    line1_rect = line1_surface.get_rect(center=(WINDOW_WIDTH // 2, META_BOX_HEIGHT*1.5 // 4))
    line2_rect = line2_surface.get_rect(center=(WINDOW_WIDTH // 2, 3 * META_BOX_HEIGHT // 4))
    
    # Blit the text to the screen
    screen.blit(line1_surface, line1_rect)
    screen.blit(line2_surface, line2_rect)

# Function to draw grid lines
def draw_grid_lines():
    """Draws grid lines on the Sokoban board."""
    for x in range(GRID_WIDTH + 1):
        pygame.draw.line(screen, WALL_COLOR, (x * TILE_SIZE, META_BOX_HEIGHT), (x * TILE_SIZE, META_BOX_HEIGHT + WINDOW_HEIGHT))
    for y in range(GRID_HEIGHT + 1):
        pygame.draw.line(screen, WALL_COLOR, (0, META_BOX_HEIGHT + y * TILE_SIZE), (WINDOW_WIDTH, META_BOX_HEIGHT + y * TILE_SIZE))

# Function to draw the game state
def draw(interpolated_agent_positions, interpolated_box_positions):
    screen.fill(BACKGROUND_COLOR)
    draw_grid_lines()

    # Draw walls
    for wall in walls:
        pygame.draw.rect(screen, WALL_COLOR, (*[i * TILE_SIZE for i in wall], TILE_SIZE, TILE_SIZE))
    pygame.draw.rect(screen, WALL_COLOR, (0, META_BOX_HEIGHT + WINDOW_HEIGHT - TILE_SIZE, WINDOW_WIDTH, TILE_SIZE))

    # Draw goals with outline
    goal_size_fraction = 0.9
    goal_size = TILE_SIZE * goal_size_fraction
    goal_center_offset = (TILE_SIZE - goal_size) // 2
    
    for goal in goals:
        pygame.draw.circle(screen, GOAL_COLOR, (
            goal[0] * TILE_SIZE + TILE_SIZE // 2,
            goal[1] * TILE_SIZE + TILE_SIZE // 2
        ), goal_size // 2)
        pygame.draw.circle(screen, OUTLINE_COLOR, (
            goal[0] * TILE_SIZE + TILE_SIZE // 2,
            goal[1] * TILE_SIZE + TILE_SIZE // 2
        ), goal_size // 2, 1)
        font = pygame.font.SysFont("Arial", 32, bold=True)
        text_surface = font.render(str(list(goals_dict.keys())[list(goals_dict.values()).index(goal)]), True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(goal[0] * TILE_SIZE + TILE_SIZE // 2, goal[1] * TILE_SIZE + TILE_SIZE // 2))
        screen.blit(text_surface, text_rect)

    # Draw box goals
    for goal in box_goals:
        position, label, is_goal = goal
        x, y = position
        box_size_fraction = 0.8
        box_size = TILE_SIZE * box_size_fraction
        box_center_offset = (TILE_SIZE - box_size) // 2

        pygame.draw.rect(screen, GOAL_COLOR, (
            x * TILE_SIZE + box_center_offset,
            y * TILE_SIZE + box_center_offset,
            box_size,
            box_size
        ))
        pygame.draw.rect(screen, OUTLINE_COLOR, (
            x * TILE_SIZE + box_center_offset,
            y * TILE_SIZE + box_center_offset,
            box_size,
            box_size
        ), 1)
        font = pygame.font.SysFont("Arial", 32, bold=True)
        text_surface = font.render(label, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2))
        screen.blit(text_surface, text_rect)

    # Draw interpolated positions of boxes with labels
    for pos, label in interpolated_box_positions:
        box_size_fraction = 0.8
        box_size = TILE_SIZE * box_size_fraction
        box_center_offset = (TILE_SIZE - box_size) // 2

        pygame.draw.rect(screen, BOX_COLOR, (
            pos[0] * TILE_SIZE + box_center_offset,
            pos[1] * TILE_SIZE + box_center_offset,
            box_size,
            box_size
        ))
        pygame.draw.rect(screen, OUTLINE_COLOR, (
            pos[0] * TILE_SIZE + box_center_offset,
            pos[1] * TILE_SIZE + box_center_offset,
            box_size,
            box_size
        ), 1)
        text_surface = font.render(label, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(pos[0] * TILE_SIZE + TILE_SIZE // 2, pos[1] * TILE_SIZE + TILE_SIZE // 2))
        screen.blit(text_surface, text_rect)

    # Draw agents
    player_radius = TILE_SIZE // 2 - 5
    outline_radius = player_radius + 1
    for idx, pos in enumerate(interpolated_agent_positions):
        center_pos = (pos[0] * TILE_SIZE + TILE_SIZE // 2, pos[1] * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(screen, OUTLINE_COLOR, center_pos, outline_radius)
        pygame.draw.circle(screen, PLAYER_COLOR, center_pos, player_radius)
        font = pygame.font.SysFont("Arial", 32, bold=True)
        text_surface = font.render(str(idx), True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=center_pos)
        screen.blit(text_surface, text_rect)

    draw_metadata_box(screen, level_name=level_meta_data['#levelname'], search_strategy=args.search_strategy, num_generated=args.num_generated, sol_length=args.sol_length, time_elapsed=args.time_elapsed)
    pygame.display.update()

# Function to execute the plan
def execute_plan():
    for idx, step in enumerate(action_plan):
        # print(f"Executing step {idx+1}/{len(action_plan)}: {step}")  # Debug statement
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Exiting...")
                pygame.quit()
                sys.exit()
        move_agents(step)
        pygame.time.wait(100)  # Adjust this delay as necessary for visibility
        # print(f"Completed step {idx+1}/{len(action_plan)}")  # Debug statement
    print("Finished executing the plan")  # Debug statement
    time.sleep(3)

# Run the plan execution
execute_plan()
