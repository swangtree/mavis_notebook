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
from __future__ import annotations
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import memory
from typing import Union

import domains.hospital.actions as actions
import domains.hospital.state as state
import domains.hospital.goal_description as goal_description
import strategies.bfs as bfs

from domains.hospital.actions import MoveAction
from domains.hospital.heuristics import HospitalAdvancedHeuristics as heuristic

# Note: This syntax below (<variable name>: <variable type>) is type hinting and is meant
# to make it easier for you to understand (now you know that `action_set` is a list of lists of
# actions!) but if it is confusing, you can just ignore it as it is only for documentation
def graph_search(
        initial_state:      state.HospitalState,
        action_set:         list[list[actions.AnyAction]],
        goal_description:   goal_description.HospitalGoalDescription,
        frontier:           bfs.FrontierBFS
    ) -> tuple[bool, list[list[actions.AnyAction]], int, float]:
    global start_time

    # Set start time
    start_time = time.time()
    iterations = 0
    frontier.prepare(goal_description)

    # Clear the parent pointer and cost in order make sure that the initial state is a root node
    initial_state.parent = None
    initial_state.path_cost = 0
    
    '''
    Implement the Graph-Search algorithm from R&N figure 3.7
    The algorithm should here return a (boolean, list[list[actions.AnyAction]], int, float) tuple, 
    where the boolean denotes whether the algorithm successfully found a plan, the list of lists 
    is the found plan, the integer is the number of states generated and the float is the amount of time
    elapsed. You can look at the print_search_status to find out how to get those quantities.

    You will need the following methods. 
    From the HospitalState class:
        state.extract_plan() - Returns the list of actions used to reach this state.
        state.get_applicable_actions(action_set) - Returns a list containing the actions applicable in the state.
        state.result(action) - Returns the new state reached by applying the action to the current state.
    From the HospitalGoalDescription class:
        goal_description.is_goal(node) - Returns true if the state is a goal state.
    From the FrontierBFS class:
        frontier.is_empty() - returns whether the frontier is emtpy
        frontier.pop() - pops the next node from the frontier, according to the search strategy
        frontier.add(state) - adds a state to the frontier, according to the search strategy
        frontier.contains(state) - checks whether the state is already present in the frontier

    Remember to look more into the different classes to see if there is any other 
    existing method that might help you out!    
    '''
    
    frontier.add(initial_state)
    
    expandedNodes = set()
    heuristicValues = {}
    
    while not frontier.is_empty():
        node = frontier.pop()  # First node is popped from the frontier
        iterations += 1 

        # Print the current state and frontier
        print(f"Current state: {node}")
        print(f"Frontier size: {frontier.size()}")

        if goal_description.is_goal(node):
            elapsed_time = time.time() - start_time  # Compute elapsed time
            return True, node.extract_plan(), iterations, elapsed_time  # Return solution

        expandedNodes.add(node)

        for action in node.get_applicable_actions(action_set):
            child = node.result(action) 

            if child not in expandedNodes and not frontier.contains(child):
                g = node.path_cost + 1
                
                # for informed search frontiers, get the heuristic value
                if hasattr(frontier, 'heuristic'):
                    h = frontier.heuristic.h(child, goal_description)
                    f = g + h
                    print(f"f(child): {f}, g(child): {g}, h(child): {h}")
                    heuristicValues[child] = (f, g, h) #Storing heuristic values
                else:
                    #for uninformed search, we don't need heuristic values
                    print(f"g(child): {g}")
                    heuristicValues[child] = (g, g, 0)
                
                frontier.add(child)  # Add child to the frontier

        print_search_status(expandedNodes, frontier, heuristicValues)

    elapsed_time = time.time() - start_time  # Compute elapsed time
    return False, [], iterations, elapsed_time  # Return failure if no solution is found

# A global variable used to keep track of the start time of the current search
start_time = 0


def print_search_status(expanded, frontier, heuristicValues, print_search_meta_data=True):
    global start_time
    
    if len(expanded) == 0:
        start_time = time.time()
    memory_usage_bytes = memory.get_usage()
    
    # Replacing the generated comma thousands separators with dots is neither pretty nor locale aware but none of
    # Pythons four different formatting facilities seems to handle this correctly!
    num_expanded = f"{len(expanded):8,d}".replace(',', '.')
    num_frontier = f"{frontier.size():8,d}".replace(',', '.')
    num_generated = f"{len(expanded) + frontier.size():8,d}".replace(',', '.')
    elapsed_time = f"{time.time() - start_time:3.3f}".replace('.', ',')
    memory_usage_mb = f"{memory_usage_bytes / (1024*1024):3.2f}".replace('.', ',')
    
    # Include f, g, and h values in the status text
    fgh_text = ""
    for state, (f, g, h) in heuristicValues.items():
        fgh_text += f"State: {state}, f: {f}, g: {g}, h: {h}\n"
    
    status_text = f"#Expanded: {num_expanded}, #Frontier: {num_frontier}, #Generated: {num_generated}," \
                  f" Time: {elapsed_time} s, Memory: {memory_usage_mb} MB\n\n{fgh_text}"
    
    if print_search_meta_data:
        print(status_text, file=sys.stderr)

    return num_generated, elapsed_time
