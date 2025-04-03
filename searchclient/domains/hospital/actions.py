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

# pos_add and pos_sub are helper methods for performing element-wise addition and subtractions on positions
# Ex: Given two positions A = (1, 2) and B = (3, 4), pos_add(A, B) == (4, 6) and pos_sub(B, A) == (2,2)
from utils import pos_add, pos_sub
from typing import Union, Tuple
import domains.hospital.state as h_state

# A dictionary mapping action names to the corresponding direction deltas2
direction_deltas = {
    'N': (-1, 0),
    'S': (1, 0),
    'E': (0, 1),
    'W': (0, -1),
}

# An action class must implement three types be a valid action:
# 1) is_applicable(self, agent_index, state) which return a boolean describing whether this action is valid for
#    the agent with 'agent_index' to perform in 'state' independently of any other action performed by other agents.
# 2) result(self, agent_index, state) which modifies the 'state' to incorporate the changes caused by the agent
#    performing the action. Since we *always* call both 'is_applicable' and 'conflicts' prior to calling 'result',
#    there is no need to check for correctness.
# 3) conflicts(self, agent_index, state) which returns information regarding potential conflicts with other actions
#    performed concurrently by other agents. More specifically, conflicts can occur with regard to the following
#    two invariants:
#    A) Two objects may not have the same destination.
#       Ex: '0  A1' where agent 0 performs Move(E) and agent 1 performs Push(W,W)
#    B) Two agents may not move the same box concurrently,
#       Ex: '0A1' where agent 0 performs Pull(W,W) and agent 1 performs Pull(E,E)
#    In order to check for these, the conflict method should return two lists:
#       a) destinations which contains all newly occupied cells.
#       b) moved_boxes which contains the current position of boxes moved during the action, i.e. their position
#          prior to being moved by the action.
# Note that 'agent_index' is the index of the agent in the state.agent_positions list which is often but *not always*
# the same as the numerical value of the agent character.


Position = Tuple[int, int] # Only for type hinting

class NoOpAction:

    def __init__(self):
        self.name = "NoOp"

    def is_applicable(self, agent_index: int,  state: h_state.HospitalState) -> bool:
        # Optimization. NoOp can never change the state if we only have a single agent
        return len(state.agent_positions) > 1

    def result(self, agent_index: int, state: h_state.HospitalState):
        pass

    def conflicts(self, agent_index: int, state: h_state.HospitalState) -> tuple[list[Position], list[Position]]:
        current_agent_position, _ = state.agent_positions[agent_index]
        destinations = [current_agent_position]
        boxes_moved = []
        return destinations, boxes_moved

    def __repr__(self) -> str:
        return self.name


class MoveAction:

    def __init__(self, agent_direction):
        self.agent_delta = direction_deltas.get(agent_direction)
        self.name = "Move(%s)" % agent_direction

    def calculate_positions(self, current_agent_position: Position) -> Position:
        return pos_add(current_agent_position, self.agent_delta)

    def is_applicable(self, agent_index: int,  state: h_state.HospitalState) -> bool:
        current_agent_position, _ = state.agent_positions[agent_index]
        new_agent_position = self.calculate_positions(current_agent_position)
        return state.free_at(new_agent_position)

    def result(self, agent_index: int, state: h_state.HospitalState):
        current_agent_position, agent_char = state.agent_positions[agent_index]
        new_agent_position = self.calculate_positions(current_agent_position)
        state.agent_positions[agent_index] = (new_agent_position, agent_char)

    def conflicts(self, agent_index: int, state: h_state.HospitalState) -> tuple[list[Position], list[Position]]:
        current_agent_position, _ = state.agent_positions[agent_index]
        new_agent_position = self.calculate_positions(current_agent_position)
        # New agent position is a destination because it is unoccupied before the action and occupied after the action.
        destinations = [new_agent_position]
        # Since a Move action never moves a box, we can just return the empty value.
        boxes_moved = []
        return destinations, boxes_moved

    def __repr__(self):
        return self.name

class PushAction:
    
    def __init__(self, move_dir_agent, move_dir_box):
        self.agent_delta = direction_deltas.get(move_dir_agent)
        self.box_delta = direction_deltas.get(move_dir_box)
        self.name = "Push(%s,%s)" % (move_dir_agent, move_dir_box)

    def calculate_positions(self, current_agent_position: Position) -> Position:
        new_agent_position = pos_add(current_agent_position, self.agent_delta)
        new_box_position = pos_add(new_agent_position, self.box_delta)
        return new_agent_position, new_box_position 

    def is_applicable(self, agent_index: int,  state: h_state.HospitalState) -> bool:
        current_agent_position, agent_char = state.agent_positions[agent_index]
        new_agent_position, new_box_position = self.calculate_positions(current_agent_position)
        # check if there is a box with the same char at the new agent position
        box_index, box_char = state.box_at(new_agent_position)
        # retrieve colors
        agent_color = state.level.colors[agent_char]
        box_color = state.level.colors[box_char] if box_index != -1 else None
        return not state.level.wall_at(new_agent_position) and state.free_at(new_box_position) \
               and box_index != -1 and agent_color == box_color

    def result(self, agent_index: int, state: h_state.HospitalState):
        current_agent_position, agent_char = state.agent_positions[agent_index]
        new_agent_position, new_box_position = self.calculate_positions(current_agent_position)
        # move agent
        state.agent_positions[agent_index] = (new_agent_position, agent_char)
        # move box
        box_index, box_char = state.box_at(new_agent_position)
        state.box_positions[box_index] = (new_box_position, box_char)

    def conflicts(self, agent_index: int, state: h_state.HospitalState) -> tuple[list[Position], list[Position]]:
        current_agent_position, _ = state.agent_positions[agent_index]
        new_agent_position, new_box_position = self.calculate_positions(current_agent_position)
        # New box position.
        destinations = [new_box_position]
        # The position of the box
        boxes_moved = [new_agent_position]
        return destinations, boxes_moved

    def __repr__(self):
        return self.name
    
direction_deltas = {
    'N': (-1, 0),
    'S': (1, 0),
    'E': (0, 1),
    'W': (0, -1),
}

class PullAction:

    # Initialize the pull action class with the direction for agent and box movements
    def __init__(self, move_dir_agent, move_dir_box):
        self.agent_delta = direction_deltas.get(move_dir_agent) # Define the delta for agent movement
        self.box_delta = direction_deltas.get(move_dir_box) # Define the delta for box movement
        self.name = "Pull(%s,%s)" % (move_dir_agent, move_dir_box) # Set the name for the action

    # Calculate new agent position and old box position based on current position
    def calculate_positions(self, current_agent_position: Position) -> Position:
        new_agent_position = pos_add(current_agent_position, self.agent_delta) # Add agent delta to current agent position for new position
        x, y = self.box_delta
        # Calculate old box position considering the direction the box will be pulled
        old_box_position = pos_add(current_agent_position, (-1 * x, -1 * y))
        return new_agent_position, old_box_position 

    # Check if pull action is applicable in the current state
    def is_applicable(self, agent_index: int,  state: h_state.HospitalState) -> bool:
        # Get current agent position and character
        current_agent_position, agent_char = state.agent_positions[agent_index]
        new_agent_position, old_box_position = self.calculate_positions(current_agent_position)
        # Get box index and character if a box exists on position
        box_index, box_char = state.box_at(old_box_position)
        # Get agent and box color
        agent_color = state.level.colors[agent_char]
        box_color = state.level.colors[box_char] if box_index != -1 else None
        # Check if new agent position is not blocked and there exists a box of the same color as the agent to pull
        return state.free_at(new_agent_position) and box_index != -1 and agent_color == box_color

    # Update state positions after performing pull action
    def result(self, agent_index: int, state: h_state.HospitalState):
        # Get current agent position and character
        current_agent_position, agent_char = state.agent_positions[agent_index]
        new_agent_position, old_box_position = self.calculate_positions(current_agent_position)
        # Update agent position after pull action
        state.agent_positions[agent_index] = (new_agent_position, agent_char)
        # Get box index and character if a box exists on position
        box_index, box_char = state.box_at(old_box_position)
        # Update box position after being pulled
        state.box_positions[box_index] = (current_agent_position, box_char)

    # Check the conflicts in the new state
    def conflicts(self, agent_index: int, state: h_state.HospitalState) -> tuple[list[Position], list[Position]]:
        # Get current agent position
        current_agent_position, _ = state.agent_positions[agent_index]
        new_agent_position, old_box_position = self.calculate_positions(current_agent_position)
        # The new box position can be a potential conflict point
        destinations = [new_agent_position]
        # The old box position is no longer blocked after the pull action
        boxes_moved = [old_box_position]
        return destinations, boxes_moved
    
    # Return name of action when object is printed
    def __repr__(self):
        return self.name


AnyAction = Union[NoOpAction, MoveAction, PushAction, PullAction] # Only for type hinting


# An action library for the multi agent pathfinding
DEFAULT_MAPF_ACTION_LIBRARY = [
    NoOpAction(),
    MoveAction("N"),
    MoveAction("S"),
    MoveAction("E"),
    MoveAction("W"),
]


# An action library for the full hospital domain
DEFAULT_HOSPITAL_ACTION_LIBRARY = [
    NoOpAction(),
    MoveAction("N"),
    MoveAction("S"),
    MoveAction("E"),
    MoveAction("W"),
    # Add Push and Pull actions here
    PushAction("N","N"),
    PushAction("N","E"),
    PushAction("N","W"),
    PushAction("S","S"),
    PushAction("S","E"),
    PushAction("S","W"),
    PushAction("E","N"),
    PushAction("E","S"),
    PushAction("E","E"),
    PushAction("W","N"),
    PushAction("W","S"),
    PushAction("W","W"),
    PullAction("N","N"),
    PullAction("N","E"),
    PullAction("N","W"),
    PullAction("S","S"),
    PullAction("S","E"),
    PullAction("S","W"),
    PullAction("E","N"),
    PullAction("E","S"),
    PullAction("E","E"),
    PullAction("W","N"),
    PullAction("W","S"),
    PullAction("W","W")
]



