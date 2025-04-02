(define (problem movie-1-3)

(:domain movie-strips-complex)

(:objects 
object_0 
object_1 
object_2 
object_3 
object_4 
)

(:init

(chips object_0)

(dip object_1)

(pop object_2)

(cheese object_3)

(crackers object_4)

(counter-at-zero)

)
(:goal

(and (movie-rewound) (counter-at-zero) 
(have-pop) 
(have-crackers) 
(have-dip) 

)

)

)
