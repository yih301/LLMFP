(define (problem movie-4-4)

(:domain movie-strips-complex)

(:objects 
object_0 
object_1 
object_2 
object_3 
object_4 
object_5 
object_6 
object_7 
object_8 
object_9 
object_10 
object_11 
object_12 
object_13 
)

(:init

(chips object_0)

(chips object_1)

(chips object_2)

(chips object_3)

(dip object_4)

(dip object_5)

(pop object_6)

(pop object_7)

(pop object_8)

(cheese object_9)

(crackers object_10)

(crackers object_11)

(crackers object_12)

(crackers object_13)

(counter-at-zero)

)
(:goal

(and (movie-rewound) (counter-at-zero) 
(have-crackers) 
(have-pop) 
(have-cheese) 
(have-chips) 

)

)

)
