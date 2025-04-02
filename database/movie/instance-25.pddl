(define (problem movie-6-4)

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

(dip object_1)

(dip object_2)

(dip object_3)

(pop object_4)

(pop object_5)

(cheese object_6)

(cheese object_7)

(cheese object_8)

(cheese object_9)

(crackers object_10)

(crackers object_11)

(crackers object_12)

(crackers object_13)

(counter-at-zero)

)
(:goal

(and (movie-rewound) (counter-at-zero) 
(have-chips) 
(have-crackers) 
(have-cheese) 
(have-pop) 

)

)

)
