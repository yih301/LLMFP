import glob
import os
import sys
from collections import namedtuple

directory = os.path.dirname('formal_planner/database/movie/')

domain_file = "domain.pddl"
problem_path = os.path.join(directory, 'instance-*.pddl')
problem_files = glob.glob(problem_path)

for problem_file in problem_files:
    description = ''
    with open(problem_file, 'r') as f:
            instance_pddl = f.read()
    for i in range(20, 0, -1):
        if 'object_{}'.format(i) in instance_pddl:
            object_count = i + 1
            break
    description += f"You have {object_count} objects. \n"
    init = instance_pddl.split('(:init\n')[1].split('\n)\n(:goal')[0]
    init = init.split('\n\n')
    for atom in init:
        if "chips " in atom:
            atom = atom.replace('(', '').replace(')', '').replace('\n', '')
            description += f"{atom.split(' ')[1]} is chips. \n"
    for atom in init:
        if "dip" in atom:
            atom = atom.replace('(', '').replace(')', '').replace('\n', '')
            description += f"{atom.split(' ')[1]} is dip. \n"
    for atom in init:
        if "pop" in atom:
            atom = atom.replace('(', '').replace(')', '').replace('\n', '')
            description += f"{atom.split(' ')[1]} is pop. \n"
    for atom in init:
        if "cheese" in atom:
            atom = atom.replace('(', '').replace(')', '').replace('\n', '')
            description += f"{atom.split(' ')[1]} is cheese. \n"
    for atom in init:
        if "crackers" in atom:
            atom = atom.replace('(', '').replace(')', '').replace('\n', '')
            description += f"{atom.split(' ')[1]} is crackers. \n"
    for atom in init:
        if "counter-at-zero" in atom:
            atom = atom.replace('(', '').replace(')', '')
            description += f"counter-at-zero is true. \n" 
    description += f"Your goal is to achieve: \n"
    
    goals = instance_pddl.split('(:goal\n')[1].replace('(and (movie-rewound) (counter-at-zero) \n', '').replace('\n)', '').split('\n')
    # import pdb; pdb.set_trace()
    description += "movie-rewound\n"   
    description += "counter-at-zero\n"   
    for goal in goals:
        if goal != '':
            goal = goal.replace('(', '').replace(')', '').replace(' ', '')
            description += goal + "\n"      
    # import pdb; pdb.set_trace()       
    nl_file = os.path.splitext(problem_file)[0] + ".nl"
    with open(nl_file, 'w') as f:
        f.write(description)