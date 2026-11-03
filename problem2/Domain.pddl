(define (domain mars-rover)
  (:requirements :strips :typing)
  (:types rover location rock bay drill)
  (:predicates
    (at ?r - rover ?l - location)
    (connected ?from - location ?to - location)
    (rock-at ?s - rock ?l - location)
    (drill-at ?d - drill ?l - location)
    (has-drill ?r - rover)
    (bay-of ?b - bay ?r - rover)
    (empty ?b - bay)
    (in-bay ?s - rock ?b - bay)
    (soft ?s - rock)
    (hard ?s - rock))

  (:action move
    :parameters (?r - rover ?from - location ?to - location)
    :precondition (and (at ?r ?from) (connected ?from ?to))
    :effect (and (not (at ?r ?from)) (at ?r ?to)))

  (:action pick-drill
    :parameters (?r - rover ?d - drill ?l - location)
    :precondition (and (at ?r ?l) (drill-at ?d ?l))
    :effect (and (has-drill ?r) (not (drill-at ?d ?l))))

  (:action collect-soft
    :parameters (?r - rover ?s - rock ?b - bay ?l - location)
    :precondition (and (at ?r ?l) (rock-at ?s ?l) (soft ?s)
                       (bay-of ?b ?r) (empty ?b))
    :effect (and (not (rock-at ?s ?l)) (not (empty ?b)) (in-bay ?s ?b)))

  (:action collect-hard
    :parameters (?r - rover ?s - rock ?b - bay ?l - location)
    :precondition (and (at ?r ?l) (rock-at ?s ?l) (hard ?s)
                       (has-drill ?r) (bay-of ?b ?r) (empty ?b))
    :effect (and (not (rock-at ?s ?l)) (not (empty ?b)) (in-bay ?s ?b)))

  (:action deposit
    :parameters (?r - rover ?s - rock ?b - bay ?l - location)
    :precondition (and (at ?r ?l) (bay-of ?b ?r) (in-bay ?s ?b))
    :effect (and (not (in-bay ?s ?b)) (empty ?b) (rock-at ?s ?l)))
)
