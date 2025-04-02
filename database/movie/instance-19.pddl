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
)

(:init

(chips object_0)

(dip object_1)

(pop object_2)

(cheese object_3)

(crackers object_4)

(crackers object_5)

(crackers object_6)

(crackers object_7)

(counter-at-zero)

)
(:goal

(and (movie-rewound) (counter-at-zero) 
(have-chips) 
(have-dip) 
(have-pop) 
(have-crackers) 

)

)

)
