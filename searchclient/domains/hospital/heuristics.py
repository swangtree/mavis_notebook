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
        self.goal_map = defaultdict(list)
        self.total_goal_count = 0
        for (goal_position, goal_letter, is_positive_literal) in level.box_goals + level.agent_goals:
            self.goal_map[goal_letter].append((goal_position, is_positive_literal))
            self.total_goal_count += 1

    def h(self, state: h_state.HospitalState, goal_description: h_goal_description.HospitalGoalDescription) -> int:
        total_distance = 0

        #calculate agent distances to their closest respective unmet goals
        for agent_pos, agent_char in state.agent_positions:
            if agent_char in self.goal_map:
                min_dist_for_agent = float('inf')
                found_unmet_goal = False
                for goal_pos, is_positive in self.goal_map[agent_char]:
                    #check if this specific goal is met
                    current_char_at_goal = state.object_at(goal_pos)
                    goal_is_met = (is_positive and current_char_at_goal == agent_char) or \
                                  (not is_positive and current_char_at_goal != agent_char)
                    
                    if not goal_is_met:
                        found_unmet_goal = True
                        distance = abs(agent_pos[0] - goal_pos[0]) + abs(agent_pos[1] - goal_pos[1])
                        min_dist_for_agent = min(min_dist_for_agent, distance)
                
                if found_unmet_goal:
                    total_distance += min_dist_for_agent

        #calculate box distances to their closest respective unmet goals
        for box_pos, box_char in state.box_positions:
             if box_char in self.goal_map:
                min_dist_for_box = float('inf')
                found_unmet_goal = False
                for goal_pos, is_positive in self.goal_map[box_char]:
                    #check if this specific goal is met
                    current_char_at_goal = state.object_at(goal_pos)
                    goal_is_met = (is_positive and current_char_at_goal == box_char) or \
                                  (not is_positive and current_char_at_goal != box_char)

                    if not goal_is_met:
                        found_unmet_goal = True
                        distance = abs(box_pos[0] - goal_pos[0]) + abs(box_pos[1] - goal_pos[1])
                        min_dist_for_box = min(min_dist_for_box, distance)

                if found_unmet_goal:
                    total_distance += min_dist_for_box

        if self.total_goal_count == 0:
            return 0
        #normalize distance by total number of goals
        return int(total_distance / self.total_goal_count)