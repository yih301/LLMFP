(define (problem movie-2-4)

(:domain movie-strips-complex)

(:objects 
object_0 
object_1 
object_2 
object_3 
object_4 
object_5 
object_6 
)

(:init

(chips object_0)

(chips object_1)

(dip object_2)

(pop object_3)

(cheese object_4)

(crackers object_5)

(crackers object_6)

(counter-at-zero)

)
(:goal

(and (movie-rewound) (counter-at-zero) 
(have-cheese) 
(have-chips) 
(have-crackers) 
(have-dip) 

)

)

)
