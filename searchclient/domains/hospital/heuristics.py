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
        self.goal_positions = []

    def preprocess(self, level: h_level.HospitalLevel):
        # This function will be called a single time prior to the search allowing us to preprocess the level such as
        # pre-computing lookup tables or other acceleration structures
        self.goal_positions = level.box_goals + level.agent_goals

    def h(self, state: h_state.HospitalState, goal_description: h_goal_description.HospitalGoalDescription) -> int:
        # your heuristic goes here...      
        totalDistance = 0

        for goalPosition, goalChar, isPositiveLiteral in goal_description.goals:
            char = state.object_at(goalPosition)
            if isPositiveLiteral and goalChar == char:
                continue
            elif not isPositiveLiteral and goalChar != char:
                continue
            
            #Calculating Manhattan distance
            for boxPosition in state.box_positions:
                if state.box_at(boxPosition) == goalChar:
                    distance = abs(boxPosition[0] - goalPosition[0]) + abs(boxPosition[1] - goalPosition[1])
                    totalDistance += distance
                    break

            for agentPosition in state.agent_positions:
                if state.agent_at(agentPosition) == goalChar:
                    distance = abs(agentPosition[0] - goalPosition[0]) + abs(agentPosition[1] - goalPosition[1])
                    totalDistance += distance
                    break

        print(f"h(state): {totalDistance}")   
        return totalDistance