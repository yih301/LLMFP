(define (problem gripper-2-5-6)
(:domain gripper-strips)
(:objects robot1 robot2 - robot
rgripper1 lgripper1 rgripper2 lgripper2 - gripper
room1 room2 room3 room4 room5 - room
ball1 ball2 ball3 ball4 ball5 ball6 - object)
(:init
(at-robby robot1 room4)
(free robot1 rgripper1)
(free robot1 lgripper1)
(at-robby robot2 room1)
(free robot2 rgripper2)
(free robot2 lgripper2)
(at ball1 room3)
(at ball2 room1)
(at ball3 room2)
(at ball4 room3)
(at ball5 room3)
(at ball6 room5)
)
(:goal
(and
(at ball1 room2)
(at ball2 room2)
(at ball3 room2)
(at ball4 room5)
(at ball5 room3)
(at ball6 room5)
)
)
)
