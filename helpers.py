import subprocess

def load_level_file_from_path(path):
    with open(path, "r") as f:
        lines = f.readlines()
        lines = list(map(lambda line: line.strip(), lines))
        return lines
  
def convert_plan_to_string(plan):
    action_plan = []
    for joint_action in plan:
        actions = []
        for action in joint_action:
            actions.append(action.name)
        #print(actions)
        action_plan.append(tuple(actions))
    return str(action_plan)

def render_plan(level_path, plan, strategy_name, heuristic_name, num_generated, elapsed_time, sol_length):

    str_plan = convert_plan_to_string(plan) #convert the plan to a string

    # this just makes sure that the meta information is displayed correctly in the visualization
    if strategy_name == 'greedy' or strategy_name == 'astar':
        strategy_name_pygame = strategy_name + ' w. ' + heuristic_name
    else:
        strategy_name_pygame = strategy_name
    
    subprocess.run(["python", 
                    "renderMAvis.py", 
                    "--level", level_path, 
                    "--plan", str_plan, 
                    "--search_strategy", strategy_name_pygame, 
                    "--num_generated", str(num_generated), 
                    "--time_elapsed", str(elapsed_time), 
                    "--sol_length", str(sol_length)])