(define (problem movie-2-5)

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

(chips object_1)

(dip object_2)

(pop object_3)

(pop object_4)

(cheese object_5)

(crackers object_6)

(crackers object_7)

(counter-at-zero)

)
(:goal

(and (movie-rewound) (counter-at-zero) 
(have-dip) 
(have-pop) 
(have-cheese) 
(have-chips) 
(have-crackers) 

)

)

)
