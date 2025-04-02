from z3 import *
import pdb
import argparse
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from openai_func import *
import json
import traceback

variables_descriptor_prompt = '''You are given a Query under a task description in natural language, and you want solve it by building an optimization problem for this task. Your job is, given access APIs and a specific natural language query, think about variables needed to encode and solve this problem with Z3 SMT solver and describe the important attributes of variables as a JSON format description. Here is an example task-output pairs to refer to:
Example task: 
You have to plan logistics to transport packages within cities via trucks and between cities via airplanes. Locations within a city are directly connected (trucks can move between any two such locations), and so are the cities. In each city there is exactly one truck and each city has one location that serves as an airport.
Here are the actions that can be performed and its preconditions and effects:
Load truck: Load a {package} into a {truck} at a {location} only if the package and the truck are both at location. After the Load truck action, the package is not at the location and is in the truck.
Load airplane: Load a {package} into an {airplane} at a {location} only if the package and the airplane are both at location. After the Load airplane action, the package is not at the location and is in the airplane.
Unload truck: Unload a {package} from a {truck} at a {location} only if the truck is at location and the package is in truck. After the Unload truck action, the package is not in the truck and is at the location.
Unload airplane: Unload a {package} from an {airplane} at a {location} only if the airplane is at location and the package is in airplane. After the Unload airplane action, the package is not in the airplane and is at the location.
Drive truck: Drive a truck from one {location_1} to another {location_2} within a {city} only if the truck is at location_1 and both location_1 and location_2 are both in city. After the Drive truck action, the truck is not at location_1 and is at location_2.
Fly airplane: Fly an airplane from one {location_1} in a city to another {location_2} in another city only if both locations are airport and the airplane is at location_1. After the Fly airplane action, the airplane is not at location_1 and is at location_2.

Query: You have 2 airplanes a0 and a1, 2 trucks t0 and t1, 2 cities c0 and c1, city c0 has location l0-0 and l0-0 is airport, city c1 has location l0-1 and l0-1 is airport, and a package p0. Initially, t0 is at location l0-0, t1 is at location l1-0, p0 is at location l1-0, a0 and a1 are at l0-0. The goal is to have p0 to be at l0-0. 
API: You can assume you already know T as the input. You have access to a update_data(solver) API that helps to update the predicate variables.
JSON description:
{
    "objects": {
        "variable_1": {
            "name": "objects",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "query",
            "value": "a dictionary that summarizes all objects in the problem: key 'package', value ['p0']; key 'airplane', value ['a0', 'a1']; key 'truck', value ['t0', 't1']; key 'city', value ['c0', 'c1']; key 'location', value ['l0-0', 'l0-1']; key 'airport', value ['l0-0', 'l0-1']",
            "specific_requirement": null
        },
    },
    "predicates": {
        "variable_2": {
            "name": "at",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "query, variable_1",
            "value": "a dictionary of boolean variables representing whether an object is at a location at timestep: keys are (package/truck/airplane, location, timestep)",
            "specific_requirement": "add constraint to initialize timestep 0 according to query, for unmentioned objects explicitly set it to be False"
        },
        "variable_3": {
            "name": "in",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "query, variable_1",
            "value": "a dictionary of boolean variables representing whether an object is in airplane or in truck: keys are [package, airplane/truck, timestep]",
            "specific_requirement": "add constraint to initialize all values to be False at timestep 0"
        },
        "variable_4": {
            "name": "in-city",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "query, variable_1",
            "value": "a dictionary of boolean variables representing whether an location is in a city: keys are [location, city, timestep]",
            "specific_requirement": "add constraint to initialize timestep 0 according to query, for unmentioned objects explicitly set it to be False"
        }
    },
    "actions": {
        "variable_5": {
            "name": "load_truck",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "variable_1",
            "value": "a dictionary of boolean variables representing whether load_truck action is performed for package, truck, location: keys are [package, truck, location, timestep]",
            "specific_requirement": null
        },
        "variable_6": {
            "name": "load_airplane",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "variable_1",
            "value": "a dictionary of boolean variables representing whether load_airplane action is performed for package, airplane, location: keys are [package, airplane, location, timestep]",
            "specific_requirement": null
        },
        "variable_7": {
            "name": "unload_truck",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "variable_1",
            "value": "a dictionary of boolean variables representing whether unload_truck action is performed for package, truck, location: keys are [package, truck, location, timestep]",
            "specific_requirement": null
        },
        "variable_8": {
            "name": "unload_airplane",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "variable_1",
            "value": "a dictionary of boolean variables representing whether unload_airplane action is performed for package, airplane, location: keys are [package, airplane, location, timestep]",
            "specific_requirement": null
        },
        "variable_9": {
            "name": "drive_truck",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "variable_1",
            "value": "a dictionary of boolean variables representing whether drive_truck action is performed for truck, location_from, location_to, city: keys are [truck, location, location, city, timestep]",
            "specific_requirement": null
        },
        "variable_10": {
            "name": "fly_airplane",
            "SMT_variable": false,
            "number_of_variables": 1,
            "data_source": "variable_1",
            "value": "a dictionary of boolean variables representing whether fly_airplane action is performed for airplane, location_from, location_to: keys are [airplane, location, location, timestep]",
            "specific_requirement": null
        }
    },
    "update": {
        "step_1": {
            "name": "action load_truck precondition and effect",
            "SMT_variable": null,
            "number_of_variables": null,
            "data_source": "query, variable_1, variable_5",
            "value": "add constraints for preconditions and effects of load_truck",
            "specific_requirement": "for each timestep t until T, for all package, truck, and location, assert that load_truck[package, truck, location, t] implies at[truck, location, t], at[package, location, t], not at[package, location, t+1], in[package, truck, t+1]"
        },
        "step_2": {
            "name": "action load_airplane precondition and effect",
            "SMT_variable": null,
            "number_of_variables": null,
            "data_source": "query, variable_1, variable_6",
            "value": "add constraints for preconditions and effects of load_airplane",
            "specific_requirement": "for each timestep t until T, for all package, airplane, and location, assert that load_airplane[package, airplane, location, t] implies at[airplane, location, t], at[package, location, t], not at[package, location, t+1], in[package, airplane, t+1]"
        },
        "step_3": {
            "name": "action unload_truck precondition and effect",
            "SMT_variable": null,
            "number_of_variables": null,
            "data_source": "query, variable_1, variable_7",
            "value": "add constraints for preconditions and effects of unload_truck",
            "specific_requirement": "for each timestep t until T, for all package, truck, and location, assert that unload_truck[package, truck, location, t] implies at[truck, location, t], in[package, truck, t], not in[package, truck, t+1], at[package, location, t+1]"
        },
        "step_4": {
            "name": "action unload_airplane precondition and effect",
            "SMT_variable": null,
            "number_of_variables": null,
            "data_source": "query, variable_1, variable_8",
            "value": "add constraints for preconditions and effects of unload_airplane",
            "specific_requirement": "for each timestep t until T, for all package, airplane, and location, assert that unload_airplane[package, airplane, location, t] implies at[airplane, location, t], in[package, airplane, t], not in[package, airplane, t+1], at[package, location, t+1]"
        },
        "step_5": {
            "name": "action drive_truck precondition and effect",
            "SMT_variable": null,
            "number_of_variables": null,
            "data_source": "query, variable_1, variable_9",
            "value": "add constraints for preconditions and effects of drive_truck",
            "specific_requirement": "for each timestep t until T, for all truck, location_from, location_to, city, assert that drive_truck[truck, location_from, location_to, city, t] implies at[truck, location_from, t], not at[truck, location_from, t+1], at[truck, location_to, t+1]"
        },
        "step_6": {
            "name": "action fly_airplane precondition and effect",
            "SMT_variable": null,
            "number_of_variables": null,
            "data_source": "query, variable_1, variable_10",
            "value": "add constraints for preconditions and effects of fly_airplane",
            "specific_requirement": "for each timestep t until T, for all airplane, location_from, location_to, assert that fly_airplane[airplane, location_from, location_to, t] implies at[airplane, location_from, t], not at[airplane, location_from, t+1], at[airplane, location_to, t+1]"
        },
        "step_7": {
            "name": "all_actions",
            "SMT_variable": false,
            "number_of_variables": "list of all actions",
            "data_source": "variable_1, variable_5, variable_6, variable_7, variable_8, variable_9, variable_10",
            "value": "for each timestep t until T, a list of all possible actions corresponding to different objects",
            "specific_requirement": "for each timestep t until T, explicitly assert ONLY ONE action per timestep"
        }
        "step_8": {
            "name": "unchanged predicate variables update",
            "SMT_variable": null,
            "number_of_variables": null,
            "data_source": "update_data(solver)",
            "value": "update at, in, in-city using update_data(solver)",
            "specific_requirement": "update data with update_data(solver)"
        },
    },
    "goal": {
        "step_9": {
            "name": null,
            "SMT_variable": null,
            "number_of_variables": null,
            "data_source": null,
            "value": null,
            "specific_requirement": "assert for timestep T, package p0 is at location l0-0"
        }
    }
}

Now, based on the example, solve the Query under new task setting and respond with similar format, please explicitly specify the action/requirement needed to fulfill query in your response:
The task is: 
You control robots, each with a left and a right gripper that can move balls between different rooms.
There are three actions defined in this domain:
move: allows a robot to move from one room to another room if the robot is at room_from. After the move action, the robot is no longer at room_from, and the robot will be at room_to.
pick: allows a robot to pick up a ball with a gripper in a room if the robot is at this room, the ball is at this room, and the gripper is free. After the pick action, the robot carry the ball, this gripper of the robot is not free, and the ball will not at the room.
drop: allows a robot to drop a ball with a gripper in a room if the robot carry this ball, the robot is at the room. After the drop action, the robot will not carry the ball, this gripper of the robot will be free, and the ball will at the room.
Query: 
{{{question}}}

API: You have access to T as the input, so do NOT re-initialize T anywhere. You have access to a update_data(solver) API that helps to update the unchanged predicate variables. Please ONLY use this API to update unchaged predicates.
Response with JSON only with no explanation. 
JSON description:
'''

code_generator_prompt = '''You are given natural language description of a PDDL problem, available APIs, and a JSON description that summarizes important variables that guide you to encode and solve the problem with SMT solver. 
Your task is to generate steps and corresponding Python codes that utilizes Z3 SMT solver to solve the problem.
For the variables summarized in the JSON description:
(1) 'name' represents the name of the variable
(2) 'SMT_variable' indicates whether you should assign it as a normal variable or an SMT variable
SMT_variable Example: price = Int('price') # Int SMT variable
                      flight_index = [Int('flight_{}_index'.format(i)) for i in range(3)] # List of Int SMT variable
                      pick_ball = Bool('pick ball') # Boolean SMT variable
Normal variable Example: price = 100
                         flight_index = [1,2,3]
(3) 'number_of_variable' represents the length of the variable
(4) 'data_source' is the source for the variable to get the data
(5) 'value' is, after you get needed data from any source, how you should assign these data to the variable
(6) 'specific_requirement' is if there are any specific requirements that needs to be considered. 

If the problem is a PDDL problem: 
(1) Stage1 (objects): This stage initializes variables to represent objects in the problem
(1) Stage2 (predicates): This stage initializes variables to represent predicates of each timestep
(2) Stage3 (actions): This stage initializes variables to represent actions for each timestep
(3) Stage4 (update): This stage conduct step-by-step update for T timestep, each step an action is performed. At last, this step update the unchanged predicate variables to remain the same as last step.
(4) Stage5 (goal): This stage asserts the goal is satisfied

Based on previous explanation, for the below problem, can you generate steps and corresponding Python codes to encode it? Do not include any explainations. You do not need to import any packages and do not need to solve the problem or print the solutions. Please process the variables and its specific requirements one by one. 
The task is: 
You control robots, each with a left and a right gripper that can move balls between different rooms.
There are three actions defined in this domain:
move: allows a robot to move from one room to another room if the robot is at room_from. After the move action, the robot is no longer at room_from, and the robot will be at room_to.
pick: allows a robot to pick up a ball with a gripper in a room if the robot is at this room, the ball is at this room, and the gripper is free. After the pick action, the robot carry the ball, this gripper of the robot is not free, and the ball will not at the room.
drop: allows a robot to drop a ball with a gripper in a room if the robot carry this ball, the robot is at the room. After the drop action, the robot will not carry the ball, this gripper of the robot will be free, and the ball will at the room.
Query: 
{{{question}}}

API: You have access to T as the input, so do NOT re-initialize T anywhere. You have access to a update_data(solver) API that helps to update the unchanged predicate variables. Please ONLY use this API to update unchaged predicates.
JSON description:
{{{variables_descriptor_response}}}
Initialize a Z3 optimizer solver = Optimize() at the beginning of the code.
Response with Python code only with no explanation. 
Code:
'''

execution_nl_prompt = '''You are given a task description in natural language, a specific natural language query, available APIs, and an execution feedback by running a Python Code that tries to solve the task. 
The task is: 
You control robots, each with a left and a right gripper that can move balls between different rooms.
There are three actions defined in this domain:
move: allows a robot to move from one room to another room if the robot is at room_from. After the move action, the robot is no longer at room_from, and the robot will be at room_to.
pick: allows a robot to pick up a ball with a gripper in a room if the robot is at this room, the ball is at this room, and the gripper is free. After the pick action, the robot carry the ball, this gripper of the robot is not free, and the ball will not at the room.
drop: allows a robot to drop a ball with a gripper in a room if the robot carry this ball, the robot is at the room. After the drop action, the robot will not carry the ball, this gripper of the robot will be free, and the ball will at the room.
Query: 
{{{question}}}

API: You have access to T as the input, so do NOT re-initialize T anywhere. You have access to a update_data(solver) API that helps to update the unchanged predicate variables. Please ONLY use this API to update unchaged predicates.

Execution feedback: {{{feedback}}}
If the execution feedback is runtime errors, please return RUNTIME ERROR for JSON: and NULL for Correctness reasoning:.
If the execution feedback is cannot find the solution, please return CANNOT FIND SOLUTION for JSON and NULL for Correctness reasoning:.
If the execution feedback is not runtime errors, the execution feedback is the solved solution for this task. Only using the information from Execution feedback (do not use predefined variables), transform the execution feedback into a JSON format task plan by filling in the JSON below:
{
    "actions": [
        action1,
        action2,
        action3,
        ...
        ],
    "num_actions": ,
}
Then explicitly answer and explain in one sentence: Does the task plan make sense and achievable in reality and meet commonsense?: 
Please include your response here with no explanations:
[[
Plan:
Correctness reasoning: 
]]
'''

self_assess_prompt = '''You are given a task and steps that tries to solve it as an optimization problem. The steps include: 
1) a JSON description that summarizes important variables that guide to encode and solve the problem with Z3 SMT solver.
2) the Python code to encode and solve the problem with Z3 SMT solver.
Your goal is to, based on the task description, specific query, available API, and runtime execution feedback (it could either be an execution error or a generated plan if there's no runtime error), assess whether the 2 steps are correct.
The task is: 
You control robots, each with a left and a right gripper that can move balls between different rooms.
There are three actions defined in this domain:
move: allows a robot to move from one room to another room if the robot is at room_from. After the move action, the robot is no longer at room_from, and the robot will be at room_to.
pick: allows a robot to pick up a ball with a gripper in a room if the robot is at this room, the ball is at this room, and the gripper is free. After the pick action, the robot carry the ball, this gripper of the robot is not free, and the ball will not at the room.
drop: allows a robot to drop a ball with a gripper in a room if the robot carry this ball, the robot is at the room. After the drop action, the robot will not carry the ball, this gripper of the robot will be free, and the ball will at the room.
Query: 
{{{question}}}

API: You have access to T as the input, so do NOT re-initialize T anywhere. You have access to a update_data(solver) API that helps to update the unchanged predicate variables. Please ONLY use this API to update unchaged predicates.

Steps to judge:
1) {{{variables_descriptor_response}}}
2) {{{code_generator_response}}}
Execution feedback: {{{feedback}}}

Based on the previous information, evaluate whether the two steps are correct:
For Step 1: Do the variables explicitly consider the query? Do the variables explicitly consider and encode all predicates, actions, updates, and goal? Does the execution result make sense and achievable in reality and meet commonsense?
For Step 2: Does the code create all needed variables? Does the code correctly initialize information from the query and specify the goal? Does the execution result make sense and achievable in reality and meet commonsense?
Please reason the correctness with task context, rate each step with a binary score: 1 is correct, 0 is incorrect, think about how to modify in detail according to task and query, and modify the step if you think it is incorrect.
For Step 1 modification, please write in JSON format. For Step 2 modification, please write in Python and do noy change the content after line 'if solver.check() == sat: '.
Your response format should be below, put NULL to How to mofify Reasoning and Modified Step if you think the step is correct, do not include extra explanation: 
[[Step 1: 
Correctness Reasoning:
Rating:
How to mofify Reasoning: 
Modified Step 1(no explanation):
END
]]
[[Step 2: 
Correctness Reasoning:
Rating:
How to mofify Reasoning:
Modified Step 2(no explanation):
END
]]
'''

direct_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The domain is: 
You control robots, each with a left and a right gripper that can move balls between different rooms.
There are three actions defined in this domain:
move: allows a robot to move from one room to another room if the robot is at room_from. After the move action, the robot is no longer at room_from, and the robot will be at room_to.
pick: allows a robot to pick up a ball with a gripper in a room if the robot is at this room, the ball is at this room, and the gripper is free. After the pick action, the robot carry the ball, this gripper of the robot is not free, and the ball will not at the room.
drop: allows a robot to drop a ball with a gripper in a room if the robot carry this ball, the robot is at the room. After the drop action, the robot will not carry the ball, this gripper of the robot will be free, and the ball will at the room.
Query: 
{{{question}}}
What is the optimal plan with minimized number of steps to achieve my goal? Just give the actions in the plan with no explanation:
'''

cot_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The domain is: 
You control robots, each with a left and a right gripper that can move balls between different rooms.
There are three actions defined in this domain:
move: allows a robot to move from one room to another room if the robot is at room_from. After the move action, the robot is no longer at room_from, and the robot will be at room_to.
pick: allows a robot to pick up a ball with a gripper in a room if the robot is at this room, the ball is at this room, and the gripper is free. After the pick action, the robot carry the ball, this gripper of the robot is not free, and the ball will not at the room.
drop: allows a robot to drop a ball with a gripper in a room if the robot carry this ball, the robot is at the room. After the drop action, the robot will not carry the ball, this gripper of the robot will be free, and the ball will at the room.
Query: 
{{{question}}}
What is the optimal plan with minimized number of steps to achieve my goal? Let's think step by step, first reason about the problem and how to solve it, and then give the actions in the plan with no explanation:
Reason: 
JSON response:
'''

code_gen_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The domain is: 
You control robots, each with a left and a right gripper that can move balls between different rooms.
There are three actions defined in this domain:
move: allows a robot to move from one room to another room if the robot is at room_from. After the move action, the robot is no longer at room_from, and the robot will be at room_to.
pick: allows a robot to pick up a ball with a gripper in a room if the robot is at this room, the ball is at this room, and the gripper is free. After the pick action, the robot carry the ball, this gripper of the robot is not free, and the ball will not at the room.
drop: allows a robot to drop a ball with a gripper in a room if the robot carry this ball, the robot is at the room. After the drop action, the robot will not carry the ball, this gripper of the robot will be free, and the ball will at the room.
Query: {{{question}}}
Please write Python code to help me find the optimal plan with minimized number of steps to achieve my goal. You can import any package and use any solver. 
At the end, save your found plan in a variable named 'feedback' as a list of actions and corresponding objects:
Please respond with code only and wrap your answer with ```python and ```:
'''

code_gen_SMT_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The domain is: 
You control robots, each with a left and a right gripper that can move balls between different rooms.
There are three actions defined in this domain:
move: allows a robot to move from one room to another room if the robot is at room_from. After the move action, the robot is no longer at room_from, and the robot will be at room_to.
pick: allows a robot to pick up a ball with a gripper in a room if the robot is at this room, the ball is at this room, and the gripper is free. After the pick action, the robot carry the ball, this gripper of the robot is not free, and the ball will not at the room.
drop: allows a robot to drop a ball with a gripper in a room if the robot carry this ball, the robot is at the room. After the drop action, the robot will not carry the ball, this gripper of the robot will be free, and the ball will at the room.
Query: {{{question}}}
Please write Python code to encode and solve it with Z3 SMT solver and help me find the plan to achieve my goal. Initialize a Z3 optimizer solver = Optimize() at the beginning of the code. You can import any package. 
At the end, save your found plan in a variable named 'feedback' as a list of actions and corresponding objects:
Please respond with code only and wrap your answer with ```python and ```:
'''

code_gen_SMT_optimal_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The domain is: 
You control robots, each with a left and a right gripper that can move balls between different rooms.
There are three actions defined in this domain:
move: allows a robot to move from one room to another room if the robot is at room_from. After the move action, the robot is no longer at room_from, and the robot will be at room_to.
pick: allows a robot to pick up a ball with a gripper in a room if the robot is at this room, the ball is at this room, and the gripper is free. After the pick action, the robot carry the ball, this gripper of the robot is not free, and the ball will not at the room.
drop: allows a robot to drop a ball with a gripper in a room if the robot carry this ball, the robot is at the room. After the drop action, the robot will not carry the ball, this gripper of the robot will be free, and the ball will at the room.
Query: {{{question}}}
Please write Python code to encode and solve it with Z3 SMT solver and help me find the optimal plan with minimized number of steps to achieve my goal. You can import any package and use any solver. 
At the end, save your found plan in a variable named 'feedback' as a list of actions and corresponding objects:
Please respond with code only and wrap your answer with ```python and ```:
'''

apis = '''
def update_data(solver):
    # for key in assertions_set.keys():
    #     solver.add(Implies(Not(Or(assertions_set[key]))))
    print('update data')
    # print(assertions_set)
    # import pdb; pdb.set_trace()
    keys = list(assertions_set.keys())
    for predicate in assertions_set.keys():
        for pre_predicates in predicate_set:
            # import pdb; pdb.set_trace()
            try:
                if str(pre_predicates)[:-2].replace('_','') == str(predicate)[:-2].replace('_','') and int(str(pre_predicates)[-2:].replace('_','')) == int(str(predicate)[-2:].replace('_',''))-1: 
                    solver.add(Implies(Not(Or(assertions_set[predicate])), predicate == pre_predicates))
                    break
            except:
                import pdb; pdb.set_trace()

def add_assertion(expr):
    try:
        if expr.decl().kind() == Z3_OP_IMPLIES:
            # print(expr)
            expr_list = expr.children()
            for child in expr_list[1].children():
                if 'Not' in str(child):
                    child = child.children()[0]
                # print(child, type(child))
                if 'adjacent' not in str(child) and str(child) not in ['False', 'True']:
                    if int(str(expr_list[0]).split('_')[-1])+1 == int(str(child).split('_')[-1]):
                        if child not in assertions_set.keys():
                            assertions_set[child] = []
                        assertions_set[child].append(expr_list[0])
                        if child not in predicate_set:
                            predicate_set.add(child)
                # except:
                #     ...
        else:
            if 'If' not in str(expr):
                # print(expr, expr.children())
                try:
                    if expr.children()[0] not in predicate_set:
                        predicate_set.add(expr.children()[0])
                except:
                    predicate_set.add(expr)
        solver.add(expr)
    except:
        solver.add(expr)
'''

def record(output_path, iter, variables_descriptor_response, code_generator_response, self_modify_response = ''):
    with open(output_path+ 'iter ' + str(iter) + '/representation.txt', 'w') as f:
        f.write(variables_descriptor_response)
    f.close()
    with open(output_path+ 'iter ' + str(iter) + '/code.txt', 'w') as f:
        f.write(code_generator_response)
    f.close()
    if self_modify_response != '':
        with open(output_path+ 'iter ' + str(iter) + '/modify.txt', 'w') as f:
            f.write(self_modify_response)
        f.close()

def step_response_checker(step_response):
    step_response = step_response.replace('```json', '')
    step_response = step_response.replace('```', '')
    return step_response

def code_response_checker(code_response):
    code_response = code_response.replace('```python', '')
    code_response = code_response.replace('```', '')
    code_response = code_response.replace('from z3 import *', '')
    code_response = code_response.replace('T = 10', '')
    code_response = code_response.replace('T = 5', '')
    code_response = code_response.replace("Here's the corrected Python code without explanations:", '')
    if 'while timestep' not in code_response:
        code_response = """    
timestep = 1
output = 'Not able to find the plan'
while timestep < 20:
    T = timestep
    print(T)
    assertions_set = {}
    predicate_set = set()
    """ + '    '.join(code_response.splitlines(True))

    if 'if solver.check() == sat:' not in code_response:
        code_response += """        
    if solver.check() == sat: 
        feedback = ''
        print("Solution found!")
        model = solver.model()
        solved_actions = []
        for k in solver.model():
            if solver.model()[k] and ('pick' in str(k) or 'drop' in str(k) or 'move' in str(k)):
                action = '_'.join(str(k).split('_'))
                solved_actions.append(action)
        solved_actions = sorted(solved_actions, key=lambda x: int(x.split('_')[-1]))
        for action in solved_actions:
            feedback += str(action) + '; '
        break
    else:
        feedback = 'cannot find a solution'
        timestep += 1"""
    return code_response.replace('solver.add', 'add_assertion')

def assess_response_checker(output_path, iter, question, assess_response, variables_descriptor_response, code_generator_response, llm = 'gpt-4o'):
    if ']]\n[[' in assess_response:
        split = assess_response.split(']]\n[[')
    else:
        split = assess_response.split(']]\n\n[[')
    step1 = split[0]
    step2 = split[1]
    if 'Rating: 0' in step1:
        variables_descriptor_response = step1.split('Modified Step 1(no explanation):')[1].split('END')[0]
        code_generator_response = Claude_response(code_generator_prompt.replace('{{{question}}}', question).replace('{{{variables_descriptor_response}}}', variables_descriptor_response))
        code_generator_response = code_response_checker(code_generator_response)
        record(output_path, iter, variables_descriptor_response, code_generator_response)
        return variables_descriptor_response, code_generator_response
    if 'Rating: 0' in step2:
        code_generator_response = step2.split('Modified Step 2(no explanation):')[1].split('END')[0]
        code_generator_response = code_response_checker(code_generator_response)
    record(output_path, iter, variables_descriptor_response, code_generator_response)
    return variables_descriptor_response, code_generator_response

def iteration(output_path, question, llm = 'gpt-4o'):
    time_record = []

    variable_start = time.time()
    variables_descriptor_response = Claude_response(variables_descriptor_prompt.replace('{{{question}}}', question))
    variable_end = time.time()
    time_record.append(variable_end - variable_start)
    variables_descriptor_response = step_response_checker(variables_descriptor_response)
    print(variables_descriptor_response)
    with open(output_path+'ori/' + 'representation.txt', 'w') as f:
        f.write(variables_descriptor_response)
    f.close()

    code_start = time.time()
    code_generator_response = Claude_response(code_generator_prompt.replace('{{{question}}}', question).replace('{{{variables_descriptor_response}}}', variables_descriptor_response))
    code_end = time.time()
    time_record.append(code_end - code_start)
    code_generator_response = code_response_checker(code_generator_response)
    print(code_generator_response)
    with open(output_path+'ori/' + 'code.txt', 'w') as f:
        f.write(code_generator_response)
    f.close()
    # pdb.set_trace()
    return variables_descriptor_response, code_generator_response, time_record

def ours(task, index, question, llm = 'gpt-4o'):
    output_path = f'output/claude/{task}/{index+1}/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        os.makedirs(output_path+'ori/')
    variables_descriptor_response, code_generator_response, time_record = iteration(output_path,question)
    iter = 0
    while iter < 5:
        time_record_iter = []
        print('--------------------ITER {}--------------------'.format(iter))
        os.makedirs(output_path+'iter ' + str(iter)+'/')
        runtime_count = 0
        while runtime_count < 5:
            local_vars = locals()
            d = dict(local_vars, **globals())
            try:
                execute_start = time.time()
                exec(apis + code_generator_response, d, d)
                execute_end = time.time()
                time_record_iter.append(execute_end - execute_start)
                feedback = d['feedback']
                if feedback == '': feedback = 'Goal already satisfied'
            except Exception as e: 
                feedback = traceback.format_exc()
            print(feedback)
            with open(output_path+ 'iter ' + str(iter) + '/feedback{}.txt'.format(runtime_count), 'w') as f:
                f.write(feedback)
            f.close()
            if 'Traceback' in feedback:
                code_generator_response = Claude_response((code_generator_prompt+ 'Your previous answer has runtime error\n').replace('{{{question}}}', question).replace('{{{variables_descriptor_response}}}', variables_descriptor_response))
                code_generator_response = code_response_checker(code_generator_response)
                print(code_generator_response)
                with open(output_path+ 'iter ' + str(iter) + 'runtime_code{}.txt'.format(runtime_count), 'w') as f:
                    f.write(code_generator_response)
                f.close()
                runtime_count += 1
            else:
                break
        execution_nl_start = time.time()
        execution_nl_response = Claude_response(execution_nl_prompt.replace('{{{question}}}', question).replace('{{{feedback}}}', feedback))
        execution_nl_end = time.time()
        time_record_iter.append(execution_nl_end - execution_nl_start)
        print(execution_nl_response)
        with open(output_path+ 'iter ' + str(iter) + '/feedback_JSON.txt', 'w') as f:
            f.write(execution_nl_response)
        f.close()
        if 'RUNTIME ERROR' in execution_nl_response:
            execution_nl_response = feedback
        # pdb.set_trace()
        assess_start = time.time()
        self_assess_response = Claude_response(self_assess_prompt.replace('{{{question}}}', question).replace('{{{variables_descriptor_response}}}', variables_descriptor_response).replace('{{{code_generator_response}}}', code_generator_response).replace('{{{feedback}}}', execution_nl_response))
        assess_end = time.time()
        time_record_iter.append(assess_end - assess_start)
        print(self_assess_response)
        with open(output_path+ 'iter ' + str(iter) + '/self_assess.txt', 'w') as f:
            f.write(self_assess_response)
        f.close()
        # pdb.set_trace()
        if 'Rating: 0' in self_assess_response:
            modify_start = time.time()
            variables_descriptor_response, code_generator_response = assess_response_checker(output_path, iter, question, self_assess_response, variables_descriptor_response, code_generator_response, llm)
            modify_end = time.time()
            time_record_iter.append(modify_end - modify_start)
            with open(output_path+'iter ' + str(iter)+'/'+ 'time.txt', 'w') as f:
                f.write(str(time_record_iter))
            f.close()
            iter += 1
        else:
            with open(output_path+ 'plan.txt', 'w') as f:
                f.write(str(feedback))
            f.close()
            with open(output_path+'iter ' + str(iter)+'/'+ 'time.txt', 'w') as f:
                f.write(str(time_record_iter))
            f.close()
            with open(output_path+ 'time.txt', 'w') as f:
                f.write(str(time_record))
            f.close()
            return
    with open(output_path+ 'plan_last.txt', 'w') as f:
        f.write(str(feedback))
    f.close()
    with open(output_path+ 'time.txt', 'w') as f:
        f.write(str(time_record))
    f.close()

def direct(task, index, question, llm = 'gpt-4o'):
    if llm == 'o1-preview':
        output_path = f'output/claude/direct_o1/{task}/{index+1}/'
    else:
        output_path = f'output/claude/direct_optimal/{task}/{index+1}/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    start = time.time()
    response = Claude_response(direct_prompt.replace('{{{question}}}', question))
    end = time.time()
    with open(output_path+ 'plan.txt', 'w') as f:
        f.write(str(response))
    f.close()
    with open(output_path+ 'time.txt', 'w') as f:
        f.write(str(end-start))
    f.close()

def CoT(task, index, question, llm = 'gpt-4o'):
    output_path = f'output/claude/CoT_optimal/{task}/{index+1}/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    start = time.time()
    response = Claude_response(cot_prompt.replace('{{{question}}}', question))
    end = time.time()
    with open(output_path+ 'plan.txt', 'w') as f:
        f.write(str(response))
    f.close()
    with open(output_path+ 'time.txt', 'w') as f:
        f.write(str(end-start))
    f.close()

def code_generation(index, question, llm = 'gpt-4o', mode = 'all'):
    if mode == 'SMT':
        output_path = f'output/claude/code_generation_SMT/{task}/{index+1}/'
    else:
        output_path = f'output/claude/code_generation_optimal/{task}/{index+1}/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    start = time.time()
    if mode == 'SMT':
        code_response = Claude_response(code_gen_SMT_prompt.replace('{{{question}}}', question))
    else:
        code_response = Claude_response(code_gen_prompt.replace('{{{question}}}', question))
    with open(output_path+ 'code.txt', 'w') as f:
        f.write(str(code_response))
    f.close()
    end = time.time()
    code_response = code_response.split('```python')[1].split('```')[0]
    local_vars = locals()
    d = dict(local_vars, **globals())
    try:
        exec(code_response, d, d)
        feedback = d['feedback']
    except:
        feedback = 'runtime error'
    with open(output_path+ 'plan.txt', 'w') as f:
        f.write(str(feedback))
    f.close()
    with open(output_path+ 'time.txt', 'w') as f:
        f.write(str(end-start))
    f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_mode", type=str, default="ours")
    parser.add_argument("--llm", type=str, default="gpt-4o")
    parser.add_argument("--index_start", type=int, default=1)
    parser.add_argument("--index_end", type=int, default=2) #total 25
    args = parser.parse_args()

    task = 'gripper'
    bench_path =  f'database/gripper/'
    answer_path =  f'database/gripper_gold_plans/'
    for i in range(args.index_start, args.index_end):
        question_path = bench_path + "instance-{}.nl".format(i+1)
        with open(question_path, 'r') as f:
            question = f.read()
        print(question)
        if args.test_mode == 'direct':
            output = direct(task, i, question, llm = args.llm)
        elif args.test_mode == 'CoT':
            output = CoT(task, i, question, llm = args.llm)
        elif args.test_mode == 'code':
            output = code_generation(i, question, llm = args.llm)
        elif args.test_mode == 'code_SMT':
                output = code_generation(i, question, llm = args.llm, mode = 'SMT')
        elif args.test_mode == 'ours':
            with open(answer_path + "instance-{}_gold_plan.txt".format(i+1), 'r') as f:
                answer = f.read()
            # pdb.set_trace()
            ours(task, i, question, llm = args.llm)
            output_path = f'output/claude/{task}/{i+1}/'
            with open(output_path+ 'query.txt', 'w') as f:
                f.write(str(question))
            f.close()
            with open(output_path+ 'answer.txt', 'w') as f:
                f.write(str(answer))
            f.close()