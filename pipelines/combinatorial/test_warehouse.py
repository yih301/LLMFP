from z3 import *
import pdb
import argparse
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from openai_func import *
import json
import traceback
import pulp
import random
import decimal

constraint_descriptor_prompt = '''You are given a task description in natural language, and you want solve it by building an optimization problem for this task.
The task is: The robots need to finish N tasks one by one by visiting N stations (repeatable) that are capable of accomplishing corresponding tasks. The robot to start at origin, finish N given tasks with given order, and return back to origin. The goal is to find the list of N stations while minimizing the total distance travelled.
You have access to function get_distance(station_1: Int(), station_2: Int()) that you can directly call to calculate the distance: Real() between two stations(you can use index 10 to represent origin).
You have access to the available stations to accomplish different tasks:
# Each row is the stations that could be used to accomplish the task
station_task_info = {
    'Task 0': [2, 3, 4, 7, 9],
    'Task 1': [1, 2],
    'Task 2': [1, 5],
    'Task 3': [3, 4],
    'Task 4': [5, 8],
    'Task 5': [0, 4, 5, 6],
    'Task 6': [3, 6, 8, 9],
    'Task 7': [0, 1],
    'Task 8': [2, 7, 8],
    'Task 9': [7, 9]
}
To get started of building the optimization problem, what is the goal, decision variables, and constraints to consider for this task?
Specifically, consider:
Goal: define the objective trying to optimize
Decision variables: identify all the decision variables involved in the problem
Constraints: key requirement for decision variables; For every pair of decision variables, carefully consider relations between them and explicitly include as constraint to ensure all variables are connected with each other
Response with [[GOAL: ]], [[Decision Variables: ]], [[Constraints Reasoning: ]], and [[Constraints: ]] only with no explanation. Do not make up ungiven information.
'''

variables_descriptor_prompt = '''You are given a Query under a task description in natural language, and you want solve it by building an optimization problem for this task. You already have considered the goal and constraints of this optimization problem. Your job is, given access to existing variables or APIs and a specific natural language query, think about other variables needed to encode and solve this problem with Z3 SMT solver and describe the important attributes of variables as a JSON format description. Here are some example task-output pairs to refer to:
Example task 1: There are blocks of different colors and scores in the scene. You need to select required number of non-repeat blocks with required color, while maximizing the score.
Query: I previously want to select 20 blocks that are black or red, but now my demand raises 9%.
GOAL: Maximize the total score of selected blocks.
Decision Variables: Indexes of blocks selected
Constraint: The required number of selected blocks is met.
Constraint: The selected blocks are non-repeat.
Constraint: The selected blocks have required color.
Variable or API: 
You have the access to function math.ceil() to round UP float to int and math.floor() to round DOWN float to int.
You have access to a BlockSearch API. BlockSearch.run(color:list) gives 1.all possible block ids of color in "color" list and 2.corresponding score info. BlockSearch.get_info(score_info, block_index) gives the score of certain block. ] 
JSON description:
{
    "variable_1": {
                            "name": "blocks", 
                            "SMT_variable": true,
                            "number_of_variables": math.ceil(20 * 1.09),
                            "data_source": "BlockSearch.run()", 
                            "value": "selecting math.ceil(20 * 1.09) blocks from black and red blocks", 
                            "specific_requirement": "selected blocks are black or red; non-repeat blocks"
                        }, 
    "variable_2": {
                            "name": "score", 
                            "SMT_variable": true,
                            "number_of_variables": math.ceil(20 * 1.09),
                            "data_source": "BlockSearch.get_info()", 
                            "value": "depends on variable_1 variables", 
                            "specific_requirement": null
                        },
    "variable_3": {
                            "name": "total_score", 
                            "SMT_variable": true,
                            "number_of_variables": 1,
                            "data_source": "variable_2 variables", 
                            "value": "sum of variable_2 variables", 
                            "specific_requirement": "equal to sum of variable_2 variables, maximize"
                        },
}

Example task 2: Given a list of cities, you need to start from an origin city, non-repeatly visit each other city exactly once, and traval back to origin city, with minimized total distance travelled. 
Query: Total number of cities is 10.
GOAL: Minimize the total travel distance.
Decision Variables: List of visited city indexes
Constraint: Start from and end with same city.
Constraint: Each city is visited exactly once and non-repeat.
Variable or API: You have access to a DistanceSearch() API. DistanceSearch.run() takes no argument and gives the distance info between cities, and DistanceSerarch.get_info(distance_info, city_1, city_2) gives the distance(a real number) between two cities.
Based on below examples, your task is to generate a JSON description to describe the problem. 
JSON description:
{
    "variable_1": {
                            "name": "cities", 
                            "SMT_variable": true,
                            "number_of_variables": 10,
                            "how_to_pick": "selecting 10 cities from 10 cities", 
                            "data_source": null, 
                            "specific_requirement": "non-repeat cities"
                        }, 
    "variable_2": {
                            "name": "distance", 
                            "SMT_variable": true,
                            "number_of_variables": 10,
                            "how_to_pick": "depends on constraint_1 variables", 
                            "data_source": "DistanceSearch.run(), DistanceSerarch.get_info()", 
                            "specific_requirement": "distance between each city pair, and the distance back to origin city"
                        },
    "variable_3": {
                            "name": "total_distance", 
                            "SMT_variable": true,
                            "number_of_variables": 1,
                            "data_source": "variable_2 variables", 
                            "value": "sum of variable_2 variables", 
                            "specific_requirement": "equal to sum of variable_2 variables, minimize"
                        },
}
Now, based on the examples, solve the Query under new task setting and respond with similar format, please explicitly specify the action/requirement needed to fulfill query, and explicitly take into consideration every constraint mentioned:
The task is: The robots need to finish N tasks one by one by visiting N stations (repeatable) that are capable of accomplishing corresponding tasks. The robot to start at origin, finish N given tasks with given order, and return back to origin. The goal is to find the list of N stations while minimizing the total distance travelled.
Query: {{{question}}}
{{{constraint_descriptor_response}}}
Variable or API: 
You have access to function get_distance(station_1: Int(), station_2: Int()) that you can directly call to calculate the distance: Real() between two stations(you can use index 10 to represent origin).
You have access to the available stations to accomplish different tasks:
# Each row is the stations that could be used to accomplish the task
station_task_info = {
    'Task 0': [2, 3, 4, 7, 9],
    'Task 1': [1, 2],
    'Task 2': [1, 5],
    'Task 3': [3, 4],
    'Task 4': [5, 8],
    'Task 5': [0, 4, 5, 6],
    'Task 6': [3, 6, 8, 9],
    'Task 7': [0, 1],
    'Task 8': [2, 7, 8],
    'Task 9': [7, 9]
}
Explicitly consider every constraint and goal and describe ALL important attributes of variables as a JSON format description. 
Make sure to explicitly consider and include requirements/constraints needed to answer the query. Note that to answer the query "Why do xxx", you need to examine the effect of "not doing xxx" to provide reasons; and to answer the query "Why not do xxx", you need to examine the effect of "do xxx" to provide reasons.
Response with JSON only with no explanation.
'''

code_generator_prompt = '''You are given a task description in natural language, a specific natural language query, available APIs and variables, and a JSON description that summarizes important variables that guide you to encode and solve the problem with SMT solver. 
Your task is to generate steps and corresponding Python codes that utilizes Z3 SMT solver to solve the problem.
For the variables summarized in the JSON description:
(1) 'name' represents the name of the variable
(2) 'SMT_variable' indicates whether you should assign it as a normal variable or an SMT variable
SMT_variable Example: price = Int('price')
                      flight_index = [Int('flight_{}_index'.format(i)) for i in range(3)]
                      pick_ball = Bool('pick ball') # Boolean SMT variable
Normal variable Example: price = 100
                         flight_index = [1,2,3]
(3) 'number_of_variable' represents the length of the variable
(4) 'data_source' is the source for the variable to get the data
(5) 'value' is, after you get needed data from any source, how you should assign these data to the variable
(6) 'specific_requirement' is if there are any specific requirements that needs to be considered. 

For the below problem, can you generate steps and corresponding Python codes to encode it? Do not include any explanations. You do not need to solve the problem or print the solutions.
The task is: The robots need to finish N tasks one by one by visiting N stations (repeatable) that are capable of accomplishing corresponding tasks. The robot to start at origin, finish N given tasks with given order, and return back to origin. The goal is to find the list of N stations while minimizing the total distance travelled.
Query: {{{question}}}
{{{constraint_descriptor_response}}}
Variable or API: 
You have access to function get_distance(station_1: Int(), station_2: Int()) that you can directly call to calculate the distance: Real() between two stations(you can use index 10 to represent origin).
You have access to the available stations to accomplish different tasks:
# Each row is the stations that could be used to accomplish the task
station_task_info = {
    'Task 0': [2, 3, 4, 7, 9],
    'Task 1': [1, 2],
    'Task 2': [1, 5],
    'Task 3': [3, 4],
    'Task 4': [5, 8],
    'Task 5': [0, 4, 5, 6],
    'Task 6': [3, 6, 8, 9],
    'Task 7': [0, 1],
    'Task 8': [2, 7, 8],
    'Task 9': [7, 9]
}
JSON variable representation: 
{{{variables_descriptor_response}}}
Please use a SMT variable named total_distance when calculating the total distance. Please put the optimization goal at the end after all needed calculation and constraints additions. 
Make sure your code add constraints to solver that considers and could answer the query. Note that to answer the query "Why do xxx", you need to examine the effect of "not doing xxx" to provide reasons; and to answer the query "Why not do xxx", you need to examine the effect of "do xxx" to provide reasons.
Initialize a Z3 optimizer solver = Optimize() at the beginning of the code.
Response with Python code only with no explanation.
'''

execution_nl_prompt = '''You are given a task description in natural language, a specific natural language query, pre-defined variables, and an execution feedback by running a Python Code that tries to solve the task. 
The task is: The robots need to finish N tasks one by one by visiting N stations (repeatable) that are capable of accomplishing corresponding tasks. The robot to start at origin, finish N given tasks with given order, and return back to origin. The goal is to find the list of N stations while minimizing the total distance travelled.
Query: {{{question}}}
Variable or API: 
You have access to function get_distance(station_1: Int(), station_2: Int()) that you can directly call to calculate the distance: Real() between two stations(you can use index 10 to represent origin).
You have access to the available stations to accomplish different tasks:
# Each row is the stations that could be used to accomplish the task
station_task_info = {
    'Task 0': [2, 3, 4, 7, 9],
    'Task 1': [1, 2],
    'Task 2': [1, 5],
    'Task 3': [3, 4],
    'Task 4': [5, 8],
    'Task 5': [0, 4, 5, 6],
    'Task 6': [3, 6, 8, 9],
    'Task 7': [0, 1],
    'Task 8': [2, 7, 8],
    'Task 9': [7, 9]
}
Execution feedback: {{{feedback}}}
If the execution feedback is runtime errors, please return RUNTIME ERROR for JSON: and NULL for Correctness reasoning:.
If the execution feedback is cannot find the solution, please return CANNOT FIND SOLUTION for JSON and NULL for Correctness reasoning:.
If the execution feedback is not runtime errors, the execution feedback is the solved solution for this task. Only using the information from Execution feedback (do not use predefined variables), transform the execution feedback into a JSON format task plan by filling in the JSON below:
{
    "IDs of the station the robot need to visit(include origin at start and end)": [],
}
In addition, for Correctness reasoning, please explicitly answer one by one does the task plan satisfy these constraints? Include one sentece explanation for each constaint:
{{{constraint_descriptor_response}}}
Then explicitly answer and explain in only ONE sentence only: Does the task plan make sense and achievable in reality and meet commonsense?: 
Please include your response here with NO explanations after this:
[[
JSON task plan:
Correctness reasoning: 
]]
'''
self_assess_prompt = '''You are given a task and steps that tries to solve it as an optimization problem. The steps include: 
1) specifying the goal and constraints of the optimization problem. Not considering query in this step.
2) a JSON description that summarizes important variables that guide to encode and solve the problem with Z3 SMT solver.
3) the Python code to encode and solve the problem with Z3 SMT solver.
Your goal is to, based on the task description, specific query, available API or variables, and runtime execution feedback (it could either be an execution error or a generated plan if there's no runtime error), assess whether any steps 1-3 are correct.
The task is: The robots need to finish N tasks one by one by visiting N stations (repeatable) that are capable of accomplishing corresponding tasks. The robot to start at origin, finish N given tasks with given order, and return back to origin. The goal is to find the list of N stations while minimizing the total distance travelled.
Query: {{{question}}}
Variable or API:
You have access to function get_distance(station_1: Int(), station_2: Int()) that you can directly call to calculate the distance: Real() between two stations(you can use index 10 to represent origin).
You have access to the available stations to accomplish different tasks:
# Each row is the stations that could be used to accomplish the task
station_task_info = {
    'Task 0': [2, 3, 4, 7, 9],
    'Task 1': [1, 2],
    'Task 2': [1, 5],
    'Task 3': [3, 4],
    'Task 4': [5, 8],
    'Task 5': [0, 4, 5, 6],
    'Task 6': [3, 6, 8, 9],
    'Task 7': [0, 1],
    'Task 8': [2, 7, 8],
    'Task 9': [7, 9]
}

Steps to judge:
Step 1) 
{{{constraint_descriptor_response}}}
Step 2) 
{{{variables_descriptor_response}}}
Step 3) 
{{{code_generator_response}}}
Execution feedback: 
{{{feedback}}}

Based on the previous information, evaluate whether steps 1-3 are correct:
For Step 1: Step 1 does NOT need to consider query. Besides, does the step consider correct goal and all needed constraints? Does the execution result make sense and achievable in reality and meet commonsense?
For Step 2: Look through ALL variables and specific requirements in the representation, does the representation consider all constraints and goal? Does the execution result make sense and achievable in reality and meet commonsense?
For Step 3: Does the code create all needed variables? Does the code make up any ungiven information? Does the execution result make sense and achievable in reality and meet commonsense?
Please reason the correctness with task context, rate each step with a binary score: 1 is correct, 0 is incorrect, think about how to modify in detail according to task and query, and modify the step if you think it is incorrect.
If no solution is found, there must be some errors and you must rate 0 for some step. 
Give 0 as rating only when you think the final answer is incorrect and the particular step is INCORRECT. Do not give 0 if you think the step is correct but could be better. 
For Step 1 modification, do NOT add information from query into it. For Step 2 modification, please write in JSON format. For Step 3 modification, please write in Python and do noy change the content after line 'if solver.check() == sat: '.
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
[[Step 3: 
Correctness Reasoning:
Rating:
How to mofify Reasoning:
Modified Step 3(no explanation):
END
]]
'''
direct_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The task is: The robots need to finish N tasks one by one by visiting N stations (repeatable) that are capable of accomplishing corresponding tasks. The robot to start at origin, finish N given tasks with given order, and return back to origin. The goal is to find the list of N stations while minimizing the total distance travelled.
Query: {{{question}}}
You have access to the available stations to accomplish different tasks and distances between stations:
# Each row is the stations that could be used to accomplish the task
station_task_info = {
    'Task 0': [2, 3, 4, 7, 9],
    'Task 1': [1, 2],
    'Task 2': [1, 5],
    'Task 3': [3, 4],
    'Task 4': [5, 8],
    'Task 5': [0, 4, 5, 6],
    'Task 6': [3, 6, 8, 9],
    'Task 7': [0, 1],
    'Task 8': [2, 7, 8],
    'Task 9': [7, 9]
}

# 11x11 distance matrix for 10 stations + origin (you can assume origin index is 10)
distances = array([[0.        , 0.27658633, 0.08      , 0.50249378, 0.66098411, 0.55901699, 0.43104524, 0.54203321, 0.74632433, 0.73498299, 0.32557641],
       [0.27658633, 0.        , 0.23259407, 0.77665951, 0.86209048, 0.83546394, 0.63600314, 0.81467785, 1.00722391, 0.99161484, 0.60108236],
       [0.08      , 0.23259407, 0.        , 0.5481788 , 0.65122961, 0.61619802, 0.51088159, 0.6074537 , 0.77472576, 0.75960516, 0.38832976],
       [0.50249378, 0.77665951, 0.5481788 , 0.        , 0.43908997, 0.12165525, 0.49040799, 0.19723083, 0.28160256, 0.28861739, 0.21095023],
       [0.66098411, 0.86209048, 0.65122961, 0.43908997, 0.        , 0.55461698, 0.87458562, 0.63631753, 0.35510562, 0.31575307, 0.560803  ],
       [0.55901699, 0.83546394, 0.61619802, 0.12165525, 0.55461698, 0.        , 0.4428318 , 0.09433981, 0.3354102 , 0.35510562, 0.23600847],
       [0.43104524, 0.63600314, 0.51088159, 0.49040799, 0.87458562, 0.4428318 , 0.        , 0.36      , 0.76655072, 0.77794601, 0.31400637],
       [0.54203321, 0.81467785, 0.6074537 , 0.19723083, 0.63631753, 0.09433981, 0.36      , 0.        , 0.42941821, 0.4494441 , 0.21954498],
       [0.74632433, 1.00722391, 0.77472576, 0.28160256, 0.35510562, 0.3354102 , 0.76655072, 0.42941821, 0.        , 0.04      , 0.49010203],
       [0.73498299, 0.99161484, 0.75960516, 0.28861739, 0.31575307, 0.35510562, 0.77794601, 0.4494441 , 0.04      , 0.        , 0.49254441],
       [0.32557641, 0.60108236, 0.38832976, 0.21095023, 0.560803  , 0.23600847, 0.31400637, 0.21954498, 0.49010203, 0.49254441, 0.        ]])
What is the plan to achieve my goal? Answer by fill in this JSON response directly with no explanation:
{
    "IDs of the station the robot need to visit(include origin at start and end)": [],
}
'''

cot_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The task is: The robots need to finish N tasks one by one by visiting N stations (repeatable) that are capable of accomplishing corresponding tasks. The robot to start at origin, finish N given tasks with given order, and return back to origin. The goal is to find the list of N stations while minimizing the total distance travelled.
Query: {{{question}}}
You have access to the available stations to accomplish different tasks and distances between stations:
# Each row is the stations that could be used to accomplish the task
station_task_info = {
    'Task 0': [2, 3, 4, 7, 9],
    'Task 1': [1, 2],
    'Task 2': [1, 5],
    'Task 3': [3, 4],
    'Task 4': [5, 8],
    'Task 5': [0, 4, 5, 6],
    'Task 6': [3, 6, 8, 9],
    'Task 7': [0, 1],
    'Task 8': [2, 7, 8],
    'Task 9': [7, 9]
}

# 11x11 distance matrix for 10 stations + origin (you can assume origin index is 10)
distances = array([[0.        , 0.27658633, 0.08      , 0.50249378, 0.66098411, 0.55901699, 0.43104524, 0.54203321, 0.74632433, 0.73498299, 0.32557641],
       [0.27658633, 0.        , 0.23259407, 0.77665951, 0.86209048, 0.83546394, 0.63600314, 0.81467785, 1.00722391, 0.99161484, 0.60108236],
       [0.08      , 0.23259407, 0.        , 0.5481788 , 0.65122961, 0.61619802, 0.51088159, 0.6074537 , 0.77472576, 0.75960516, 0.38832976],
       [0.50249378, 0.77665951, 0.5481788 , 0.        , 0.43908997, 0.12165525, 0.49040799, 0.19723083, 0.28160256, 0.28861739, 0.21095023],
       [0.66098411, 0.86209048, 0.65122961, 0.43908997, 0.        , 0.55461698, 0.87458562, 0.63631753, 0.35510562, 0.31575307, 0.560803  ],
       [0.55901699, 0.83546394, 0.61619802, 0.12165525, 0.55461698, 0.        , 0.4428318 , 0.09433981, 0.3354102 , 0.35510562, 0.23600847],
       [0.43104524, 0.63600314, 0.51088159, 0.49040799, 0.87458562, 0.4428318 , 0.        , 0.36      , 0.76655072, 0.77794601, 0.31400637],
       [0.54203321, 0.81467785, 0.6074537 , 0.19723083, 0.63631753, 0.09433981, 0.36      , 0.        , 0.42941821, 0.4494441 , 0.21954498],
       [0.74632433, 1.00722391, 0.77472576, 0.28160256, 0.35510562, 0.3354102 , 0.76655072, 0.42941821, 0.        , 0.04      , 0.49010203],
       [0.73498299, 0.99161484, 0.75960516, 0.28861739, 0.31575307, 0.35510562, 0.77794601, 0.4494441 , 0.04      , 0.        , 0.49254441],
       [0.32557641, 0.60108236, 0.38832976, 0.21095023, 0.560803  , 0.23600847, 0.31400637, 0.21954498, 0.49010203, 0.49254441, 0.        ]])
What is the plan to achieve my goal? Let's think step by step, first reason about the problem and how to solve it, then answer by fill in the JSON:
Reason: 
JSON response:
{
    "IDs of the station the robot need to visit(include origin at start and end)": [],
}
'''

code_gen_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The task is: The robots need to finish N tasks one by one by visiting N stations (repeatable) that are capable of accomplishing corresponding tasks. The robot to start at origin, finish N given tasks with given order, and return back to origin. The goal is to find the list of N stations while minimizing the total distance travelled.
Query: {{{question}}}
You have access to function get_distance(station_1: int(), station_2: int()) that you can directly call to calculate the distance: real() between two stations(you can use index 10 to represent origin)
You have access to the available stations to accomplish different tasks and distances between stations:
# Each row is the stations that could be used to accomplish the task
station_task_info = {
    'Task 0': [2, 3, 4, 7, 9],
    'Task 1': [1, 2],
    'Task 2': [1, 5],
    'Task 3': [3, 4],
    'Task 4': [5, 8],
    'Task 5': [0, 4, 5, 6],
    'Task 6': [3, 6, 8, 9],
    'Task 7': [0, 1],
    'Task 8': [2, 7, 8],
    'Task 9': [7, 9]
}
Please write Python code to help me find the plan to achieve my goal. You can import any package and use any solver. 
At the end, save your found plan in a variable named 'feedback' with the following format:
JSON response:
{
    "IDs of the station the robot need to visit(include origin at start and end)": [],
}
Please respond with code only and wrap your answer with ```python and ```:
'''

code_gen_SMT_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The task is: The robots need to finish N tasks one by one by visiting N stations (repeatable) that are capable of accomplishing corresponding tasks. The robot to start at origin, finish N given tasks with given order, and return back to origin. The goal is to find the list of N stations while minimizing the total distance travelled.
Query: {{{question}}}
You have access to function get_distance(station_1: Int(), station_2: Int()) that you can directly call to calculate the distance: Real() between two stations(you can use index 10 to represent origin)
You have access to the available stations to accomplish different tasks and distances between stations:
# Each row is the stations that could be used to accomplish the task
station_task_info = {
    'Task 0': [2, 3, 4, 7, 9],
    'Task 1': [1, 2],
    'Task 2': [1, 5],
    'Task 3': [3, 4],
    'Task 4': [5, 8],
    'Task 5': [0, 4, 5, 6],
    'Task 6': [3, 6, 8, 9],
    'Task 7': [0, 1],
    'Task 8': [2, 7, 8],
    'Task 9': [7, 9]
}
Please write Python code to encode and solve it with Z3 SMT solver and help me find the plan to achieve my goal. Initialize a Z3 optimizer solver = Optimize() at the beginning of the code. You can import any package. 
At the end, save your found plan in a variable named 'feedback' with the following format:
JSON response:
{
    "IDs of the station the robot need to visit(include origin at start and end)": [],
}
Please respond with code only and wrap your answer with ```python and ```:
'''

def get_data(benchQA):
    questions = []
    answers = []
    for i in range(len(benchQA['questions'])):
        questions.append(benchQA['questions'][i]['QUESTION'])
        answers.append(benchQA['questions'][i]['GT EXEC RESULT'])
    return questions, answers

def record(output_path, iter, constraint_descriptor_response, variables_descriptor_response, code_generator_response, self_modify_response = ''):
    with open(output_path+ 'iter ' + str(iter) + '/constraints.txt', 'w') as f:
        f.write(constraint_descriptor_response)
    f.close()
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

def execute(code_response):
    # Each row is the stations that could be used to accomplish the task
    station_task_info = {
        'Task 0': [2, 3, 4, 7, 9],
        'Task 1': [1, 2],
        'Task 2': [1, 5],
        'Task 3': [3, 4],
        'Task 4': [5, 8],
        'Task 5': [0, 4, 5, 6],
        'Task 6': [3, 6, 8, 9],
        'Task 7': [0, 1],
        'Task 8': [2, 7, 8],
        'Task 9': [7, 9]
    }

    # Each row is the coordinate of origin and each station
    # coordinates = {
    #     'Origin': [0.5, 0.5],
    #     'Station 0': [0.74, 0.72],
    #     'Station 1': [0.92, 0.93],
    #     'Station 2': [0.82, 0.72],
    #     'Station 3': [0.48, 0.29],
    #     'Station 4': [0.86, 0.07],
    #     'Station 5': [0.36, 0.31],
    #     'Station 6': [0.31, 0.75],
    #     'Station 7': [0.31, 0.39],
    #     'Station 8': [0.51, 0.01],
    #     'Station 9': [0.55, 0.01]
    # }
    coordinates = [
       [0.74, 0.72],
       [0.92, 0.93],
       [0.82, 0.72],
       [0.48, 0.29],
       [0.86, 0.07],
       [0.36, 0.31],
       [0.31, 0.75],
       [0.31, 0.39],
       [0.51, 0.01],
       [0.55, 0.01],
       [0.5, 0.5]
       ]
    def run_distance():
        results = Array('station_distances', IntSort(), IntSort(), RealSort())
        z = np.array([[complex(*c) for c in coordinates]])
        distance_matrix = np.abs(z.T - z)
        for i in range(11):
            for j in range(11):
                distance = distance_matrix[i, j]
                results = Store(results, i, j, distance)
        return results
    
    def get_distance(city_1, city_2):
        info_key = Select(distance_smt_matrix, city_1, city_2)
        return info_key
    
    distance_smt_matrix = run_distance()


    # Note: this is for non-SMT method
    # def get_distance(index1, index2):
    #     z = np.array([[complex(*c) for c in coordinates]])
    #     distance_matrix = np.abs(z.T - z)
    #     # pdb.set_trace()
    #     return distance_matrix[index1, index2]
    
    local_vars = locals()
    d = dict(local_vars, **globals())
    try:
        exec(code_response, d, d)
        return d['feedback']
    except Exception as e: 
        print(e)
        return traceback.format_exc()

def constraint_response_checker(constraint_descriptor_response):
    constraint_descriptor_response = constraint_descriptor_response.replace('[[', '').replace(']]', '')
    constraints = 'Constraints: ' + constraint_descriptor_response.split('Constraints Reasoning:')[1].split('Constraints:')[1]
    return constraint_descriptor_response.split('Constraints Reasoning:')[0] + constraints
    
def step_response_checker(step_response):
    step_response = step_response.replace('```json', '')
    step_response = step_response.replace('```', '')
    return step_response

def code_response_checker(code_response):
    code_response = code_response.replace('```python', '')
    code_response = code_response.replace('```', '')
    if 'if solver.check() == sat:' not in code_response:
        code_response += """        
if solver.check() == sat: 
    print('solution found')
    feedback = str(sorted ([(k, solver.model()[k]) for k in solver.model()], key = lambda x: str(x[0])))
else:
    feedback = 'cannot find a solution'"""
    return code_response

def assess_response_checker(output_path, iter, question, assess_response, constraint_descriptor_response, variables_descriptor_response, code_generator_response, llm = 'gpt-4o'):
    if ']]\n[[' in assess_response:
        split = assess_response.split(']]\n[[')
    else:
        split = assess_response.split(']]\n\n[[')
    step1 = split[0]
    step2 = split[1]
    step3 = split[2]
    if 'Rating: 0' in step1:
        try:
            constraint_descriptor_response = step1.split('Modified Step 1(no explanation):')[1].split('END')[0]
        except: 
            pdb.set_trace()
        variables_descriptor_response = Claude_response(variables_descriptor_prompt.replace('{{{question}}}', question).replace('{{{constraint_descriptor_response}}}', constraint_descriptor_response))
        variables_descriptor_response = step_response_checker(variables_descriptor_response)
        code_generator_response = Claude_response(code_generator_prompt.replace('{{{question}}}', question).replace('{{{constraint_descriptor_response}}}', constraint_descriptor_response).replace('{{{variables_descriptor_response}}}', variables_descriptor_response))
        code_generator_response = code_response_checker(code_generator_response)
        record(output_path, iter, constraint_descriptor_response, variables_descriptor_response, code_generator_response)
        return constraint_descriptor_response, variables_descriptor_response, code_generator_response
    if 'Rating: 0' in step2:
        variables_descriptor_response = step2.split('Modified Step 2(no explanation):')[1].split('END')[0]
        code_generator_response = Claude_response(code_generator_prompt.replace('{{{question}}}', question).replace('{{{constraint_descriptor_response}}}', constraint_descriptor_response).replace('{{{variables_descriptor_response}}}', variables_descriptor_response))
        code_generator_response = code_response_checker(code_generator_response)
        record(output_path, iter, constraint_descriptor_response, variables_descriptor_response, code_generator_response)
        return constraint_descriptor_response, variables_descriptor_response, code_generator_response
    if 'Rating: 0' in step3:
        code_generator_response = step3.split('Modified Step 3(no explanation):')[1].split('END')[0]
        code_generator_response = code_response_checker(code_generator_response)
    record(output_path, iter, constraint_descriptor_response, variables_descriptor_response, code_generator_response)
    return constraint_descriptor_response, variables_descriptor_response, code_generator_response

def iteration(output_path, question, constraint_descriptor_response = '', variables_descriptor_response = '', mode = 'all', llm = 'gpt-4o'):
    time_record = []
    constraint_start = time.time()
    constraint_descriptor_response = Claude_response(constraint_descriptor_prompt.replace('{{{question}}}', question))
    constraint_end = time.time()
    time_record.append(constraint_end - constraint_start)
    print(constraint_descriptor_response)
    constraint_descriptor_response = constraint_response_checker(constraint_descriptor_response) # constraint_descriptor_response.replace('[[', '').replace(']]', '')
    # print(constraint_descriptor_response)
    # pdb.set_trace()
    with open(output_path+'ori/' + 'constraints.txt', 'w') as f:
        f.write(constraint_descriptor_response)
    f.close()

    variable_start = time.time()
    variables_descriptor_response = Claude_response(variables_descriptor_prompt.replace('{{{question}}}', question).replace('{{{constraint_descriptor_response}}}', constraint_descriptor_response))
    variable_end = time.time()
    time_record.append(variable_end - variable_start)
    variables_descriptor_response = step_response_checker(variables_descriptor_response)
    print(variables_descriptor_response)
    with open(output_path+'ori/' + 'representation.txt', 'w') as f:
        f.write(variables_descriptor_response)
    f.close()

    code_start = time.time()
    code_generator_response = Claude_response(code_generator_prompt.replace('{{{question}}}', question).replace('{{{constraint_descriptor_response}}}', constraint_descriptor_response).replace('{{{variables_descriptor_response}}}', variables_descriptor_response))
    code_end = time.time()
    time_record.append(code_end - code_start)
    code_generator_response = code_response_checker(code_generator_response)
    print(code_generator_response)
    with open(output_path+'ori/' + 'code.txt', 'w') as f:
        f.write(code_generator_response)
    f.close()
    return constraint_descriptor_response, variables_descriptor_response, code_generator_response, time_record

def ours(task, index, question, llm = 'gpt-4o'):
    output_path = f'output/claude/{task}/{index}/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        os.makedirs(output_path+'ori/')
    constraint_descriptor_response, variables_descriptor_response, code_generator_response, time_record = iteration(output_path,question)
    iter = 0
    while iter < 5:
        time_record_iter = []
        print('--------------------ITER {}--------------------'.format(iter))
        os.makedirs(output_path+'iter ' + str(iter)+'/')
        runtime_count = 0
        while runtime_count < 5:
            execute_start = time.time()
            feedback = execute(code_generator_response)
            execute_end = time.time()
            time_record_iter.append(execute_end - execute_start)
            print(feedback)
            with open(output_path+ 'iter ' + str(iter) + '/feedback{}.txt'.format(runtime_count), 'w') as f:
                f.write(feedback)
            f.close()
            if 'Traceback' in feedback:
                code_generator_response = Claude_response((code_generator_prompt+ 'Your previous answer has runtime error\n').replace('{{{question}}}', question).replace('{{{constraint_descriptor_response}}}', constraint_descriptor_response).replace('{{{variables_descriptor_response}}}', variables_descriptor_response))
                code_generator_response = code_response_checker(code_generator_response)
                print(code_generator_response)
                with open(output_path+ 'iter ' + str(iter) + 'runtime_code{}.txt'.format(runtime_count), 'w') as f:
                    f.write(code_generator_response)
                f.close()
                runtime_count += 1
            else:
                break
        execution_nl_start = time.time()
        execution_nl_response = Claude_response(execution_nl_prompt.replace('{{{question}}}', question).replace('{{{constraint_descriptor_response}}}', constraint_descriptor_response).replace('{{{feedback}}}', feedback))
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
        self_assess_response = Claude_response(self_assess_prompt.replace('{{{question}}}', question).replace('{{{constraint_descriptor_response}}}', constraint_descriptor_response).replace('{{{variables_descriptor_response}}}', variables_descriptor_response).replace('{{{code_generator_response}}}', code_generator_response).replace('{{{feedback}}}', execution_nl_response))
        assess_end = time.time()
        time_record_iter.append(assess_end - assess_start)
        print(self_assess_response)
        with open(output_path+ 'iter ' + str(iter) + '/self_assess.txt', 'w') as f:
            f.write(self_assess_response)
        f.close()
        # pdb.set_trace()
        if 'Rating: 0' in self_assess_response:
            modify_start = time.time()
            constraint_descriptor_response, variables_descriptor_response, code_generator_response = assess_response_checker(output_path, iter, question, self_assess_response, constraint_descriptor_response, variables_descriptor_response, code_generator_response, llm)
            modify_end = time.time()
            time_record_iter.append(modify_end - modify_start)
            with open(output_path+'iter ' + str(iter)+'/'+ 'time.txt', 'w') as f:
                f.write(str(time_record_iter))
            f.close()
            iter += 1
        else:
            result_list = feedback.split('), (')
            total_distance = feedback
            for result in result_list:
                if 'total_distance' in result:
                    total_distance = result.replace('total_distance, ', '').replace(')', '').replace(']', '').replace('[', '').replace('(', '')
            with open(output_path+ 'total_distance.txt', 'w') as f:
                f.write(str(total_distance))
            f.close()
            with open(output_path+'iter ' + str(iter)+'/'+ 'time.txt', 'w') as f:
                f.write(str(time_record_iter))
            f.close()
            with open(output_path+ 'time.txt', 'w') as f:
                f.write(str(time_record))
            f.close()
            return total_distance
    result_list = feedback.split('), (')
    total_distance = feedback
    for result in result_list:
        if 'total_distance' in result:
            total_distance = result.replace('total_distance, ', '').replace(')', '').replace(']', '').replace('[', '').replace('(', '')
    with open(output_path+ 'total_distance_last.txt', 'w') as f:
        f.write(str(total_distance))
    f.close()
    with open(output_path+ 'time.txt', 'w') as f:
        f.write(str(time_record))
    f.close()
    return total_distance
    
def direct(index, question, llm = 'gpt-4o'):
    output_path = f'output/claude/direct/warehouse/{index+1}/'
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

def CoT(index, question, llm = 'gpt-4o'):
    output_path = f'output/claude/CoT/warehouse/{index}/'
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
        output_path = f'output/code_generation_SMT/warehouse/{index}/'
    else:
        output_path = f'output/code_generation/warehouse/{index}/'
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
    feedback = execute(code_response)
    with open(output_path+ 'plan.txt', 'w') as f:
        f.write(str(feedback))
    f.close()
    with open(output_path+ 'time.txt', 'w') as f:
        f.write(str(end-start))
    f.close()

def run_task(tasks) -> dict:
    station_tasks = [
        [5, 7],
        [7, 1, 2],
        [0, 1, 8],
        [3, 0, 6],
        [0, 5, 3],
        [4, 2, 5],
        [5, 6],
        [8, 9, 0],
        [4, 8, 6],
        [9, 0, 6]
        ] # 10 x 3
    station_lists = []
    for i, task in enumerate(tasks):
        station_list = []
        for j, station_task in enumerate(station_tasks):
            for station in station_task:
                if task == station and j not in station_list:
                    station_list.append(j)
        if len(station_list) == 0: station_list.append(0)
        station_lists.append(station_list)
    return station_lists

def min_travel_distance(task_ids):
    from functools import lru_cache
    import math

    coordinates = [
       [0.74, 0.72],
       [0.92, 0.93],
       [0.82, 0.72],
       [0.48, 0.29],
       [0.86, 0.07],
       [0.36, 0.31],
       [0.31, 0.75],
       [0.31, 0.39],
       [0.51, 0.01],
       [0.55, 0.01],
       [0.5, 0.5]
       ]
    z = np.array([[complex(*c) for c in coordinates]])
    distance_matrix = np.abs(z.T - z)
    station_task_list = run_task(task_ids)
    print(station_task_list)

    num_tasks = len(task_ids)

    @lru_cache(None)
    def dp(task_index, pos):
        if task_index == num_tasks:
            return (distance_matrix[pos][10], [pos, 10])  # Return to starting point

        min_dist = math.inf
        best_path = []

        # Try to go to any station for the current task
        for next_station in station_task_list[task_index]:
            dist, path = dp(task_index + 1, next_station)
            total_dist = distance_matrix[pos][next_station] + dist
            if total_dist < min_dist:
                min_dist = total_dist
                best_path = [pos] + path

        return (min_dist, best_path)

    # Initial state: Start at station 0 with the first task
    min_distance, visit_path = dp(0, 10)

    # Remove the initial position from visit_path to get only the task-related path
    visit_path = visit_path[:-1]  # Remove the last 0 (starting point) from the end

    return min_distance, visit_path

def calculate_distance(stations, task_ids):
    coordinates = [
       [0.74, 0.72],
       [0.92, 0.93],
       [0.82, 0.72],
       [0.48, 0.29],
       [0.86, 0.07],
       [0.36, 0.31],
       [0.31, 0.75],
       [0.31, 0.39],
       [0.51, 0.01],
       [0.55, 0.01],
       [0.5, 0.5]
       ]
    station_lists = run_task(task_ids)
    for i, station_list in enumerate(station_lists):
        if stations[i+1] not in station_list:
            return -1
    total_distance = 0
    z = np.array([[complex(*c) for c in coordinates]])
    distance_matrix = np.abs(z.T - z)
    # pdb.set_trace()
    for i in range(len(stations)-1):
        total_distance += distance_matrix[stations[i]][stations[i+1]]
    total_distance += distance_matrix[0][1]
    total_distance += distance_matrix[-1][0]
    return total_distance

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_mode", type=str, default="ours")
    parser.add_argument("--llm", type=str, default="claude")
    parser.add_argument("--index_start", type=int, default=0)
    parser.add_argument("--index_end", type=int, default=5) # total 50
    args = parser.parse_args()

    task = 'warehouse'
    count = 0
    iter_count = [0,0,0,0,0]
    feasible = 0
    for i in range(args.index_start, args.index_end):
        np.random.seed(i)
        random.seed(i)
        total_task_number = 10
        task_number = np.random.randint(3, 10)
        # task_ids = np.random.randint(total_task_number, size = task_number)
        task_ids = random.sample(range(total_task_number), task_number)
        question = f'Number of Tasks is {task_number}. The Task ids needs to be accomplished are: {str(task_ids)}'
        if args.test_mode == 'direct':
            output = direct(i, question, llm = args.llm)
        elif args.test_mode == 'CoT':
            output = CoT(i, question, llm = args.llm)
        elif args.test_mode == 'code':
            output = code_generation(i, question, llm = args.llm)
        elif args.test_mode == 'code_SMT':
            output = code_generation(i, question, llm = args.llm, mode = 'SMT')
        elif args.test_mode == 'ours':
            output = ours(task, i, question, llm = args.llm)
            output_path = f'output/claude/{task}/{i}/'
            with open(output_path+ 'query.txt', 'w') as f:
                f.write(str(question))
            f.close()
        # elif args.test_mode == 'optimal':
            min_distance, visit_path = min_travel_distance(task_ids)
            print(min_distance, visit_path)
            optimal = calculate_distance(visit_path + [10], task_ids)
            # pdb.set_trace()
            output_path = f'output/claude/{task}/{i}/'
            with open(output_path+ 'optimal_answer.txt', 'w') as f:
                f.write(str(min_distance))
            f.close()
            with open(output_path+ 'optimal_path.txt', 'w') as f:
                f.write(str(visit_path+ [10]))
            f.close()




