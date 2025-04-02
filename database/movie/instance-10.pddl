(define (problem movie-3-5)

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

(dip object_1)

(pop object_2)

(pop object_3)

(pop object_4)

(cheese object_5)

(cheese object_6)

(crackers object_7)

(crackers object_8)

(counter-at-zero)

)
(:goal

(and (movie-rewound) (counter-at-zero) 
(have-crackers) 
(have-chips) 
(have-dip) 
(have-pop) 
(have-cheese) 

)

)

)
