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


constraint_descriptor_prompt = '''You are given a task description in natural language, and you want solve it by building an optimization problem for this task.
The task is: Given a list of tasks (Number_A Task A, Number_B Task B, Number_C Task C) and three heterogeneous robots (Robot A, Robot B, Robot C) that are skilled at different tasks, the goal is to find the way to assign different number of tasks to different robots and finish the tasks with minimized finish time. The three robots could work in parallel, but the finish time counts the time when the last robot stops working. 
You have the access to variables that summarized the skill (finish time) of each robot to accomplish each type of task and original task number for each type:
# Finish time for each robot-task pair
robot_work_time_for_tasks = {
    ('Robot A', 'Task A'): 24,
    ('Robot A', 'Task B'): 89,
    ('Robot A', 'Task C'): 38,
    ('Robot B', 'Task A'): 27,
    ('Robot B', 'Task B'): 58,
    ('Robot B', 'Task C'): 56,
    ('Robot C', 'Task A'): 18,
    ('Robot C', 'Task B'): 57,
    ('Robot C', 'Task C'): 49,
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
The task is: Given a list of tasks (Number_A Task A, Number_B Task B, Number_C Task C) and three heterogeneous robots (Robot A, Robot B, Robot C) that are skilled at different tasks, the goal is to find the way to assign different number of tasks to different robots and finish the tasks with minimized finish time. The three robots could work in parallel, but the finish time counts the time when the last robot stops working. 
Query: {{{question}}}
{{{constraint_descriptor_response}}}
Variable or API: 
You have access to a Max(variable_list) function that takes a list as input and outputs the max of this list of variables.
You have the access to variables that summarized the skill (finish time) of each robot to accomplish each task:
# Finish time for each robot-task pair
robot_work_time_for_tasks = {
    ('Robot A', 'Task A'): 24,
    ('Robot A', 'Task B'): 89,
    ('Robot A', 'Task C'): 38,
    ('Robot B', 'Task A'): 27,
    ('Robot B', 'Task B'): 58,
    ('Robot B', 'Task C'): 56,
    ('Robot C', 'Task A'): 18,
    ('Robot C', 'Task B'): 57,
    ('Robot C', 'Task C'): 49,
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
The task is: Given a list of tasks (Number_A Task A, Number_B Task B, Number_C Task C) and three heterogeneous robots (Robot A, Robot B, Robot C) that are skilled at different tasks, the goal is to find the way to assign different number of tasks to different robots and finish the tasks with minimized finish time. The three robots could work in parallel, but the finish time counts the time when the last robot stops working. 
Query: {{{question}}}
{{{constraint_descriptor_response}}}
Variable or API: 
You have access to a Max(variable_list) function that takes a list as input and outputs the max of this list of variables.
You have the access to variables that summarized the skill (finish time) of each robot to accomplish each task:
# Finish time for each robot-task pair
robot_work_time_for_tasks = {
    ('Robot A', 'Task A'): 24,
    ('Robot A', 'Task B'): 89,
    ('Robot A', 'Task C'): 38,
    ('Robot B', 'Task A'): 27,
    ('Robot B', 'Task B'): 58,
    ('Robot B', 'Task C'): 56,
    ('Robot C', 'Task A'): 18,
    ('Robot C', 'Task B'): 57,
    ('Robot C', 'Task C'): 49,
}
JSON variable representation: 
{{{variables_descriptor_response}}}
Please use a SMT variable named max_finish_time when calculating the maximum spent time for all robots to finish. Please put the optimization goal at the end after all needed calculation and constraints additions. 
Make sure your code add constraints to solver that considers and could answer the query. Note that to answer the query "Why do xxx", you need to examine the effect of "not doing xxx" to provide reasons; and to answer the query "Why not do xxx", you need to examine the effect of "do xxx" to provide reasons.
Initialize a Z3 optimizer solver = Optimize() at the beginning of the code.
Response with Python code only with no explanation.
'''

execution_nl_prompt = '''You are given a task description in natural language, a specific natural language query, pre-defined variables, and an execution feedback by running a Python Code that tries to solve the task. 
The task is: Given a list of tasks (Number_A Task A, Number_B Task B, Number_C Task C) and three heterogeneous robots (Robot A, Robot B, Robot C) that are skilled at different tasks, the goal is to find the way to assign different number of tasks to different robots and finish the tasks with minimized finish time. The three robots could work in parallel, but the finish time counts the time when the last robot stops working. 
Query: {{{question}}}
Variable or API: 
You have access to a Max(variable_list) function that takes a list as input and outputs the max of this list of variables.
You have the access to variables that summarized the skill (finish time) of each robot to accomplish each task:
# Finish time for each robot-task pair
robot_work_time_for_tasks = {
    ('Robot A', 'Task A'): 24,
    ('Robot A', 'Task B'): 89,
    ('Robot A', 'Task C'): 38,
    ('Robot B', 'Task A'): 27,
    ('Robot B', 'Task B'): 58,
    ('Robot B', 'Task C'): 56,
    ('Robot C', 'Task A'): 18,
    ('Robot C', 'Task B'): 57,
    ('Robot C', 'Task C'): 49,
}
Execution feedback: {{{feedback}}}
If the execution feedback is runtime errors, please return RUNTIME ERROR for JSON: and NULL for Correctness reasoning:.
If the execution feedback is cannot find the solution, please return CANNOT FIND SOLUTION for JSON and NULL for Correctness reasoning:.
If the execution feedback is not runtime errors, the execution feedback is the solved solution for this task. Only using the information from Execution feedback (do not use predefined variables), transform the execution feedback into a JSON format task plan by filling in the JSON below:
{
    "Robot A task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot B task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot C task assignment": {'Task A': , 'Task B':, 'Task C': },
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
The task is: Given a list of tasks (Number_A Task A, Number_B Task B, Number_C Task C) and three heterogeneous robots (Robot A, Robot B, Robot C) that are skilled at different tasks, the goal is to find the way to assign different number of tasks to different robots and finish the tasks with minimized finish time. The three robots could work in parallel, but the finish time counts the time when the last robot stops working. 
Query: {{{question}}}
Variable or API:
You have access to a Max(variable_list) function that takes a list as input and outputs the max of this list of variables.
You have the access to variables that summarized the skill (finish time) of each robot to accomplish each task:
# Finish time for each robot-task pair
robot_work_time_for_tasks = {
    ('Robot A', 'Task A'): 24,
    ('Robot A', 'Task B'): 89,
    ('Robot A', 'Task C'): 38,
    ('Robot B', 'Task A'): 27,
    ('Robot B', 'Task B'): 58,
    ('Robot B', 'Task C'): 56,
    ('Robot C', 'Task A'): 18,
    ('Robot C', 'Task B'): 57,
    ('Robot C', 'Task C'): 49,
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
The domain is: Given a list of tasks (Number_A Task A, Number_B Task B, Number_C Task C) and three heterogeneous robots (Robot A, Robot B, Robot C) that are skilled at different tasks, the goal is to find the way to assign different number of tasks to different robots and finish the tasks with minimized finish time. The three robots could work in parallel, but the finish time counts the time when the last robot stops working. 
Query: {{{question}}}
You have the access to variables that summarized the skill (finish time) of each robot to accomplish each task:
# Finish time for each robot-task pair
robot_work_time_for_tasks = {
    ('Robot A', 'Task A'): 24,
    ('Robot A', 'Task B'): 89,
    ('Robot A', 'Task C'): 38,
    ('Robot B', 'Task A'): 27,
    ('Robot B', 'Task B'): 58,
    ('Robot B', 'Task C'): 56,
    ('Robot C', 'Task A'): 18,
    ('Robot C', 'Task B'): 57,
    ('Robot C', 'Task C'): 49,
}
What is the plan to achieve my goal? Answer by fill in this JSON response directly with no explanation:
{
    "Robot A task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot B task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot C task assignment": {'Task A': , 'Task B':, 'Task C': },
}
'''

cot_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The domain is: Given a list of tasks (Number_A Task A, Number_B Task B, Number_C Task C) and three heterogeneous robots (Robot A, Robot B, Robot C) that are skilled at different tasks, the goal is to find the way to assign different number of tasks to different robots and finish the tasks with minimized finish time. The three robots could work in parallel, but the finish time counts the time when the last robot stops working. 
Query: {{{question}}}
You have the access to variables that summarized the skill (finish time) of each robot to accomplish each task:
# Finish time for each robot-task pair
robot_work_time_for_tasks = {
    ('Robot A', 'Task A'): 24,
    ('Robot A', 'Task B'): 89,
    ('Robot A', 'Task C'): 38,
    ('Robot B', 'Task A'): 27,
    ('Robot B', 'Task B'): 58,
    ('Robot B', 'Task C'): 56,
    ('Robot C', 'Task A'): 18,
    ('Robot C', 'Task B'): 57,
    ('Robot C', 'Task C'): 49,
}
What is the plan to achieve my goal? Let's think step by step, first reason about the problem and how to solve it, then answer by fill in the JSON:
Reason: 
JSON response:
{
    "Robot A task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot B task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot C task assignment": {'Task A': , 'Task B':, 'Task C': },
}
'''

code_gen_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The domain is: Given a list of tasks (Number_A Task A, Number_B Task B, Number_C Task C) and three heterogeneous robots (Robot A, Robot B, Robot C) that are skilled at different tasks, the goal is to find the way to assign different number of tasks to different robots and finish the tasks with minimized finish time. The three robots could work in parallel, but the finish time counts the time when the last robot stops working. 
Query: {{{question}}}
You have the access to variables that summarized the skill (finish time) of each robot to accomplish each task:
# Finish time for each robot-task pair
robot_work_time_for_tasks = {
    ('Robot A', 'Task A'): 24,
    ('Robot A', 'Task B'): 89,
    ('Robot A', 'Task C'): 38,
    ('Robot B', 'Task A'): 27,
    ('Robot B', 'Task B'): 58,
    ('Robot B', 'Task C'): 56,
    ('Robot C', 'Task A'): 18,
    ('Robot C', 'Task B'): 57,
    ('Robot C', 'Task C'): 49,
}
Please write Python code to help me find the plan to achieve my goal. You can import any package and use any solver. 
At the end, save your found plan in a variable named 'feedback' with the following format:
JSON response:
{
    "Robot A task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot B task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot C task assignment": {'Task A': , 'Task B':, 'Task C': },
}
Please respond with code only and wrap your answer with ```python and ```:
'''

code_gen_SMT_prompt = '''
You have a domain and a query under this domain that you need to fulfill. 
The domain is: Given a list of tasks (Number_A Task A, Number_B Task B, Number_C Task C) and three heterogeneous robots (Robot A, Robot B, Robot C) that are skilled at different tasks, the goal is to find the way to assign different number of tasks to different robots and finish the tasks with minimized finish time. The three robots could work in parallel, but the finish time counts the time when the last robot stops working. 
Query: {{{question}}}
You have access to a Max(variable_list) function that takes a list as input and outputs the max of this list of variables.
You have the access to variables that summarized the skill (finish time) of each robot to accomplish each task:
# Finish time for each robot-task pair
robot_work_time_for_tasks = {
    ('Robot A', 'Task A'): 24,
    ('Robot A', 'Task B'): 89,
    ('Robot A', 'Task C'): 38,
    ('Robot B', 'Task A'): 27,
    ('Robot B', 'Task B'): 58,
    ('Robot B', 'Task C'): 56,
    ('Robot C', 'Task A'): 18,
    ('Robot C', 'Task B'): 57,
    ('Robot C', 'Task C'): 49,
}
Please write Python code to encode and solve it with Z3 SMT solver and help me find the plan to achieve my goal. Initialize a Z3 optimizer solver = Optimize() at the beginning of the code. You can import any package. 
At the end, save your found plan in a variable named 'feedback' with the following format:
JSON response:
{
    "Robot A task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot B task assignment": {'Task A': , 'Task B':, 'Task C': },
    "Robot C task assignment": {'Task A': , 'Task B':, 'Task C': },
}
Please respond with code only and wrap your answer with ```python and ```:
'''

def Max(vs):
  m = vs[0]
  for v in vs[1:]:
    m = If(v > m, v, m)
  return m

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
    robot_work_time_for_tasks = {
        ('Robot A', 'Task A'): 24,
        ('Robot A', 'Task B'): 89,
        ('Robot A', 'Task C'): 38,
        ('Robot B', 'Task A'): 27,
        ('Robot B', 'Task B'): 58,
        ('Robot B', 'Task C'): 56,
        ('Robot C', 'Task A'): 18,
        ('Robot C', 'Task B'): 57,
        ('Robot C', 'Task C'): 49,
    }
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
            max_finish_time = feedback
            for result in result_list:
                if 'max_finish_time' in result:
                    max_finish_time = result.replace('max_finish_time, ', '').replace(')', '').replace(']', '').replace('[', '').replace('(', '')
            with open(output_path+ 'max_finish_time.txt', 'w') as f:
                f.write(str(max_finish_time))
            f.close()
            with open(output_path+'iter ' + str(iter)+'/'+ 'time.txt', 'w') as f:
                f.write(str(time_record_iter))
            f.close()
            with open(output_path+ 'time.txt', 'w') as f:
                f.write(str(time_record))
            f.close()
            return max_finish_time
    result_list = feedback.split('), (')
    max_finish_time = feedback
    for result in result_list:
        if 'max_finish_time' in result:
            max_finish_time = result.replace('max_finish_time, ', '').replace(')', '').replace(']', '').replace('[', '').replace('(', '')
        f.write(str(max_finish_time))
    f.close()
    with open(output_path+ 'time.txt', 'w') as f:
        f.write(str(time_record))
    f.close()
    return max_finish_time
    # return 'no solution'
    
def direct(index, question, llm = 'gpt-4o'):
    output_path = f'output/claude/direct/task_allocation/{index+1}/'
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
    output_path = f'output/claude/CoT/task_allocation/{index}/'
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
        output_path = f'output/code_generation_SMT/task_allocation/{index}/'
    else:
        output_path = f'output/code_generation/task_allocation/{index}/'
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
    
def minimize_finish_time(task_number):
    # Number of robots and tasks
    num_robots = 3
    num_tasks = 3
    skill = [24,89,38,27,58,56,18,57,49]

    # Create the LP problem
    prob = pulp.LpProblem("Minimize_Finish_Time", pulp.LpMinimize)

    # Define the decision variables
    x = [[pulp.LpVariable(f'x_{i}_{j}', lowBound=0, cat='Integer') for j in range(num_tasks)] for i in range(num_robots)]
    T = pulp.LpVariable('T', lowBound=0, cat='Continuous')

    # Objective function: Minimize the maximum finish time T
    prob += T

    # Constraints: Each task should be assigned exactly as per task_number
    for j in range(num_tasks):
        prob += (pulp.lpSum([x[i][j] for i in range(num_robots)]) == task_number[j], f"Task_{j}_assignment")

    # Constraints: The finish time for each robot should not exceed T
    for i in range(num_robots):
        prob += (pulp.lpSum([x[i][j] * skill[i*num_tasks + j] for j in range(num_tasks)]) <= T, f"Robot_{i}_time")

    # Solve the problem
    prob.solve()

    # Extract the results
    assignment = [[pulp.value(x[i][j]) for j in range(num_tasks)] for i in range(num_robots)]
    finish_time = pulp.value(T)

    return assignment, finish_time 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_mode", type=str, default="ours")
    parser.add_argument("--llm", type=str, default="claude")
    parser.add_argument("--index_start", type=int, default=0)
    parser.add_argument("--index_end", type=int, default=5) #total 50
    args = parser.parse_args()

    task = 'task_allocation'
    count = 0
    iter_count = [0,0,0,0,0]
    feasible = 0
    for i in range(args.index_start, args.index_end):
        np.random.seed(i)
        task_number = np.random.randint(10, 100, size = 3)
        question = f'Number of Task A is {task_number[0]}; Number of Task B is {task_number[1]}; Number of Task C is {task_number[2]}.'
        # print(question)
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
            assignment, finish_time = minimize_finish_time(task_number)
            output_path = f'output/claude/{task}/{i}/'
            with open(output_path+ 'optimal_answer.txt', 'w') as f:
                f.write(str(finish_time))
            f.close()