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
        totalDistance = 0

        for (agentPosition, agentChar) in state.agent_positions:
            if agentChar in self.goal_dict:
                goalPosition, is_positive_literal = self.goal_dict[agentChar]
                if is_positive_literal and agentChar == state.object_at(goalPosition):
                    continue
                else:
                    totalDistance += abs(agentPosition[0] - goalPosition[0]) + abs(agentPosition[1] - goalPosition[1])
            #else:
                #print(f"DEBUG: Agent {agentChar} not in goal_dict")

        #print(f"h(state): {totalDistance}, normalized distance: {totalDistance/len(self.goal_dict)}")   
        return totalDistance/len(self.goal_dict)