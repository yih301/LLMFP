(define (problem movie-3-3)

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
)

(:init

(chips object_0)

(chips object_1)

(dip object_2)

(pop object_3)

(cheese object_4)

(cheese object_5)

(crackers object_6)

(crackers object_7)

(crackers object_8)

(counter-at-zero)

)
(:goal

(and (movie-rewound) (counter-at-zero) 
(have-chips) 
(have-pop) 
(have-crackers) 

)

)

)
