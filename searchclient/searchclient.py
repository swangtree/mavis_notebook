# coding: utf-8
#
# Copyright 2021 The Technical University of Denmark
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import argparse
import memory
import re
import sys
from agent_types.classic import classic_agent_type
from domains.hospital import *
from strategies.bfs import FrontierBFS
from strategies.dfs import FrontierDFS
from strategies.bestfirst import FrontierAStar, FrontierGreedy

from utils import read_line

def validate_memory_arg(max_memory):
    match = re.match(r"([0-9]+)g", max_memory)
    if match:
        return int(match.group(1)) * 1024 * 1024 * 1024
    else:
        raise ValueError(f"Invalid memory format: {max_memory}. Use a format like '4g'.")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Search-client for MAvis using state-space graph search.')
    parser.add_argument('--max-memory', default="4g", help='Maximum memory usage in GB (default: 4g).')
    parser.add_argument('-level', help="Load level file directly from the file system.")
    parser.add_argument('-render', action='store_true', help="Render the plan using the sokoban.py script.")

    strategy_group = parser.add_mutually_exclusive_group()
    strategy_group.add_argument('-bfs', action='store_const', dest='strategy', const='bfs')
    strategy_group.add_argument('-dfs', action='store_const', dest='strategy', const='dfs')
    strategy_group.add_argument('-astar', action='store_const', dest='strategy', const='astar')
    strategy_group.add_argument('-greedy', action='store_const', dest='strategy', const='greedy')

    heuristic_group = parser.add_mutually_exclusive_group()
    heuristic_group.add_argument('-goalcount', action='store_const', dest='heuristic', const='goalcount')
    heuristic_group.add_argument('-advancedheuristic', action='store_const', dest='heuristic', const='advanced')

    action_library_group = parser.add_mutually_exclusive_group()
    action_library_group.add_argument('-defaultactions', action='store_const', dest='action_library', const='default')

    agent_type_group = parser.add_mutually_exclusive_group()
    agent_type_group.add_argument('-classic', action='store_const', dest='agent_type', const='classic')

    args = parser.parse_args()

    args.memory_limit = validate_memory_arg(args.max_memory)
    return args

def load_level_file_from_server():
    lines = []
    while True:
        line = read_line()
        lines.append(line)
        if line.startswith("#end"):
            break
    return lines

def load_level_file_from_path(path):
    with open(path, "r") as f:
        lines = f.readlines()
        lines = list(map(lambda line: line.strip(), lines))
        return lines

if __name__ == '__main__':
    args = parse_arguments()

    strategy_name = args.strategy or 'bfs'
    heuristic_name = args.heuristic or 'goalcount'
    action_library_name = args.action_library or 'default'
    agent_type_name = args.agent_type or 'classic' # will always be classic unless you implement other agent types

    # strategy_name_pygame
    if strategy_name == 'greedy' or strategy_name == 'astar':
        strategy_name_pygame = strategy_name + ' w. ' + heuristic_name
    else:
        strategy_name_pygame = strategy_name

    # Make sure the level file is provided
    assert args.level, "No level file provided, please try again."
    level_path = args.level

    # Do not render by default
    render = args.render

    # Load level file and get domain name
    level_lines = load_level_file_from_path(level_path)
    domain_name = level_lines[1]

    # instead of using else/elif
    level, initial_state, action_library, goal_description, heuristic = None, None, None, None, None

    if domain_name == 'hospital':
        level = HospitalLevel.parse_level_lines(level_lines)
        initial_state = HospitalState(level, level.initial_agent_positions, level.initial_box_positions)
        goal_description = HospitalGoalDescription(level, level.box_goals + level.agent_goals)

        if action_library_name == 'default':
            action_library = DEFAULT_HOSPITAL_ACTION_LIBRARY

        if heuristic_name == 'goalcount':
            heuristic = HospitalGoalCountHeuristics()
        elif heuristic_name == 'advanced':
            heuristic = HospitalAdvancedHeuristics()

    if heuristic:
        heuristic.preprocess(level)

    # Initialize frontier, if no strategy is provided (then strategy_name is None), use BFS
    frontier = {
        'bfs': FrontierBFS,
        'dfs': FrontierDFS,
        'astar': lambda: FrontierAStar(heuristic),
        'greedy': lambda: FrontierGreedy(heuristic)
    }.get(strategy_name, FrontierBFS)()


    # The agent type is the only thing that is not domain specific but will almost always be classic unless you implement other agent types
    if agent_type_name == 'classic':
        str_plan, num_generated, elapsed_time, sol_length = classic_agent_type(level, initial_state, action_library, goal_description, frontier)
        
        if render:
            subprocess.run(["python3", "renderMAvis.py", "--level", level_path, "--plan", str_plan, "--search_strategy", strategy_name_pygame, "--num_generated", str(num_generated), "--time_elapsed", str(elapsed_time), "--sol_length", str(sol_length)])
    else:
        print(f"Unrecognized agent type: {agent_type_name}", file=sys.stderr)