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
import sys
import itertools
import numpy as np
from utils import pos_add, pos_sub, APPROX_INFINITY
from collections import deque, defaultdict

import domains.hospital.state as h_state
import domains.hospital.goal_description as h_goal_description
import domains.hospital.level as h_level


class HospitalZeroHeuristic:
    def __init__(self):
        pass

    def preprocess(self, level: h_level.HospitalLevel):
        # This function will be called a single time prior 
        # to the search allowing us to preprocess the level such as
        # pre-computing lookup tables or other acceleration structures
        pass

    def h(self, state: h_state.HospitalState, 
                goal_description: h_goal_description.HospitalGoalDescription) -> int:
        return 0
    

class HospitalGoalCountHeuristics:
    def __init__(self):
        pass

    def preprocess(self, level: h_level.HospitalLevel):
        self.goal_count = len(level.box_goals + level.agent_goals)
    
    def h(self, state: h_state.HospitalState, 
                goal_description: h_goal_description.HospitalGoalDescription) -> int:
        
        objects_in_goals = 0
        
        for (goal_position, goal_char, is_positive_literal) in goal_description.goals:
            char = state.object_at(goal_position)
            if is_positive_literal and goal_char == char:
                objects_in_goals += 1
            elif not is_positive_literal and goal_char != char:
                objects_in_goals += 1

        return self.goal_count - objects_in_goals

class HospitalAdvancedHeuristics:

    def __init__(self):
        pass

    def preprocess(self, level: h_level.HospitalLevel):
        # This function will be called a single time prior to the search allowing us to preprocess the level such as
        # pre-computing lookup tables or other acceleration structures
        self.goal_dict = {}
        for (goal_position, goal_letter, is_positive_literal) in level.box_goals + level.agent_goals:
            self.goal_dict[goal_letter] = (goal_position, is_positive_literal)
        #print(f"goal_dict: {self.goal_dict}")

    def h(self, state: h_state.HospitalState, goal_description: h_goal_description.HospitalGoalDescription) -> int:
        total_distance = 0

        #calculate agent distances from goals
        for (agent_position, agent_char) in state.agent_positions:
            if agent_char in self.goal_dict:
                goal_position, is_positive_literal = self.goal_dict[agent_char]
                if is_positive_literal and agent_char == state.object_at(goal_position):
                    continue
                else:
                    total_distance += abs(agent_position[0] - goal_position[0]) + abs(agent_position[1] - goal_position[1])
            #else:
                #print(f"DEBUG: Agent {agent_char} not in goal_dict")

        #calculate distances from boxes to their goals
        for (box_position, box_char) in state.box_positions:
            if box_char in self.goal_dict:
                goal_position, is_positive_literal = self.goal_dict[box_char]
                if is_positive_literal and box_char == state.object_at(goal_position):
                    continue
                else:
                    total_distance += abs(box_position[0] - goal_position[0]) + abs(box_position[1] - goal_position[1])
            #else:
                #print(f"DEBUG: Box {box_char} not in goal_dict")

        #print(f"h(state): {total_distance}, normalized distance: {total_distance/len(self.goal_dict)}")   
        return total_distance/len(self.goal_dict)