(define (problem gripper-1-4-7)
(:domain gripper-strips)
(:objects robot1 - robot
rgripper1 lgripper1 - gripper
room1 room2 room3 room4 - room
ball1 ball2 ball3 ball4 ball5 ball6 ball7 - object)
(:init
(at-robby robot1 room3)
(free robot1 rgripper1)
(free robot1 lgripper1)
(at ball1 room4)
(at ball2 room4)
(at ball3 room3)
(at ball4 room4)
(at ball5 room3)
(at ball6 room2)
(at ball7 room4)
)
(:goal
(and
(at ball1 room1)
(at ball2 room2)
(at ball3 room1)
(at ball4 room1)
(at ball5 room1)
(at ball6 room1)
(at ball7 room4)
)
)
)
