:- use_module(library(lists)).

% Step 1: Predicate logic representation
fol(1, all(X, all(R, implies(and(archivist(X), verifies(X, R)), trusted(X))))).
fol(2, all(X, all(R, implies(and(trusted(X), and(access(X, R), sealed(R))), permitted(X, R))))).
fol(3, all(X, all(R, implies(and(inspects(X, R), finds_mark(X, R)), verifies(X, R))))).
fol(4, all(R, implies(stored(R, royal_archive), sealed(R)))).
fol(5, stored(scroll_7, royal_archive)).
fol(6, access(mira, scroll_7)).
fol(7, and(inspects(mira, scroll_7), finds_mark(mira, scroll_7))).
fol(8, archivist(mira)).

% Step 2: Negation of goal
goal(trusted(mira)).
negated_goal(not(Goal)) :- goal(Goal).

% Step 3: Implication removal
remove_implications(implies(A, B), or(not(C), D)) :- !,
    remove_implications(A, C), remove_implications(B, D).
remove_implications(and(A, B), and(C, D)) :- !,
    remove_implications(A, C), remove_implications(B, D).
remove_implications(or(A, B), or(C, D)) :- !,
    remove_implications(A, C), remove_implications(B, D).
remove_implications(not(A), not(B)) :- !, remove_implications(A, B).
remove_implications(all(X, A), all(X, B)) :- !, remove_implications(A, B).
remove_implications(exists(X, A), exists(X, B)) :- !, remove_implications(A, B).
remove_implications(A, A).

% Step 4: Negation movement
nnf(not(not(A)), B) :- !, nnf(A, B).
nnf(not(and(A, B)), or(C, D)) :- !, nnf(not(A), C), nnf(not(B), D).
nnf(not(or(A, B)), and(C, D)) :- !, nnf(not(A), C), nnf(not(B), D).
nnf(not(all(X, A)), exists(X, B)) :- !, nnf(not(A), B).
nnf(not(exists(X, A)), all(X, B)) :- !, nnf(not(A), B).
nnf(and(A, B), and(C, D)) :- !, nnf(A, C), nnf(B, D).
nnf(or(A, B), or(C, D)) :- !, nnf(A, C), nnf(B, D).
nnf(all(X, A), all(X, B)) :- !, nnf(A, B).
nnf(exists(X, A), exists(X, B)) :- !, nnf(A, B).
nnf(A, A).

% Step 5: Standardization
standardize(A, B) :- standardize(A, [], B).
standardize(A, Env, B) :- var(A), !, bound_variable(A, Env, B).
standardize(all(X, A), Env, all(Y, B)) :- !, standardize(A, [X-Y|Env], B).
standardize(exists(X, A), Env, exists(Y, B)) :- !, standardize(A, [X-Y|Env], B).
standardize(A, _, A) :- atomic(A), !.
standardize(A, Env, B) :- A =.. [F|Args],
    maplist(standardize_with(Env), Args, NewArgs), B =.. [F|NewArgs].
standardize_with(Env, A, B) :- standardize(A, Env, B).
bound_variable(X, [Old-New|_], New) :- X == Old, !.
bound_variable(X, [_|Rest], Y) :- bound_variable(X, Rest, Y).

% Step 6: Skolemization
skolemize(A, B) :- copy_term(A, Copy), skolemize(Copy, [], B).
skolemize(all(X, A), Universals, B) :- !,
    append(Universals, [X], Next), skolemize(A, Next, B).
skolemize(exists(X, A), Universals, B) :- !,
    flag(skolem_count, N, N + 1), atomic_list_concat([skolem_, N], Name),
    X =.. [Name|Universals], skolemize(A, Universals, B).
skolemize(and(A, B), U, and(C, D)) :- !, skolemize(A, U, C), skolemize(B, U, D).
skolemize(or(A, B), U, or(C, D)) :- !, skolemize(A, U, C), skolemize(B, U, D).
skolemize(A, _, A).

% Step 7: CNF clauses
cnf(and(A, B), Clauses) :- !, cnf(A, Left), cnf(B, Right), append(Left, Right, Clauses).
cnf(or(A, B), Clauses) :- !, cnf(A, Left), cnf(B, Right),
    distribute(Left, Right, Clauses).
cnf(not(A), [[neg(A)]]) :- !.
cnf(A, [[pos(A)]]).
distribute([], _, []).
distribute([L|Ls], Right, Clauses) :-
    distribute_row(L, Right, Row), distribute(Ls, Right, Rest), append(Row, Rest, Clauses).
distribute_row(_, [], []).
distribute_row(L, [R|Rs], [Clause|Rest]) :-
    append(L, R, Combined), sort(Combined, Clause), distribute_row(L, Rs, Rest).

transformation_stages(Stages, Clauses) :-
    findall(F, fol(_, F), Facts), negated_goal(Negated), append(Facts, [Negated], Initial),
    maplist(remove_implications, Initial, WithoutImplications),
    maplist(nnf, WithoutImplications, Normal), maplist(standardize, Normal, Standard),
    flag(skolem_count, _, 0), maplist(skolemize, Standard, Skolem),
    maplist(cnf, Skolem, Nested), append(Nested, Clauses),
    Stages = [fol-Initial, implication_removal-WithoutImplications,
              negation_movement-Normal, standardization-Standard,
              skolemization_and_universal_removal-Skolem].

% Step 8: Resolution implementation and execution
complement(pos(A), neg(B), A, B).
complement(neg(A), pos(B), A, B).

resolve(Left, Right, Resolvent, Pivot, Substitution) :-
    copy_term(Left, L), copy_term(Right, R), term_variables(L-R, Variables),
    select(A, L, RestL), select(B, R, RestR),
    complement(A, B, P, Q), copy_term(P-Q, Pivot),
    copy_term(Variables, Before), unify_with_occurs_check(P, Q),
    copy_term(Variables, After), Substitution = Before-After,
    append(RestL, RestR, Combined), sort(Combined, Resolvent).

number_clauses([], _, []).
number_clauses([Clause|Rest], Id, [clause(Id, Clause)|Entries]) :-
    Next is Id + 1, number_clauses(Rest, Next, Entries).

variant_present(Clause, Entries) :- member(clause(_, Old), Entries), Clause =@= Old, !.

refute(Entries, Next, Trace, EmptyId) :-
    member(clause(GoalId, [neg(trusted(mira))]), Entries),
    refute_support(Entries, [GoalId], Next, Trace, EmptyId).

refute_support(Entries, Support, Next, Trace, EmptyId) :-
    findall(Size-candidate(I, J, Pivot, Substitution, New),
            (member(clause(I, C1), Entries), member(clause(J, C2), Entries), I < J,
             (memberchk(I, Support) -> true ; memberchk(J, Support)),
             resolve(C1, C2, New, Pivot, Substitution),
             \+ variant_present(New, Entries), length(New, Size)), Candidates),
    keysort(Candidates, [_-candidate(I, J, Pivot, Substitution, New)|_]),
    ( New == [] -> Trace = [step(Next, I, J, Pivot, Substitution, New)], EmptyId = Next
    ; append(Entries, [clause(Next, New)], Updated), N is Next + 1,
      Trace = [step(Next, I, J, Pivot, Substitution, New)|Rest],
      refute_support(Updated, [Next|Support], N, Rest, EmptyId)
    ).

proof(Clauses, Trace, EmptyId) :-
    transformation_stages(_, Clauses), number_clauses(Clauses, 1, Entries),
    length(Clauses, Count), Next is Count + 1, refute(Entries, Next, Trace, EmptyId).

show_term(Term) :- copy_term(Term, Copy), numbervars(Copy, 0, _),
    write_term(Copy, [numbervars(true), quoted(true)]).

print_clauses([], _).
print_clauses([Clause|Rest], Id) :-
    format('C~d: ', [Id]), show_term(Clause), nl,
    Next is Id + 1, print_clauses(Rest, Next).

print_step(step(Id, I, J, Pivot, Substitution, New)) :-
    format('C~d = resolve(C~d, C~d)~n  pivot before unification: ', [Id, I, J]),
    show_term(Pivot), format('~n  variable values before-after: '), show_term(Substitution),
    format('~n  resolvent: '), show_term(New), nl.

verify_trace(Clauses, Trace, EmptyId) :-
    number_clauses(Clauses, 1, Entries), verify_steps(Trace, Entries, Final),
    member(clause(EmptyId, []), Final).
verify_steps([], Entries, Entries).
verify_steps([step(Id, I, J, _, _, New)|Rest], Entries, Final) :-
    member(clause(I, Left), Entries), member(clause(J, Right), Entries),
    once((resolve(Left, Right, Candidate, _, _), Candidate =@= New)),
    append(Entries, [clause(Id, New)], Updated), verify_steps(Rest, Updated, Final).

self_test :-
    proof(Clauses, Trace, EmptyId), verify_trace(Clauses, Trace, EmptyId),
    nth1(1, Clauses, First),
    First =@= [neg(archivist(A)), neg(verifies(A, _Record)), pos(trusted(A))],
    nth1(3, Clauses, Third),
    Third =@= [neg(finds_mark(C, D)), neg(inspects(C, D)), pos(verifies(C, D))],
    \+ member([pos(trusted(mira))], Clauses),
    \+ unify_with_occurs_check(X, f(X)),
    resolve([pos(p(Y)), neg(q(Y))], [neg(p(a))], [neg(q(a))], _, _),
    forall(member(Removed, [7, 8, 9]),
           (nth1(Removed, Clauses, _, Reduced),
            number_clauses(Reduced, 1, Entries), length(Reduced, N), Next is N + 1,
            \+ refute(Entries, Next, _, _))),
    writeln('SELF-TEST PASS: replayed proof, no assumed goal, unification, required facts.').

main :-
    writeln('ROYAL ARCHIVE: RESOLUTION REFUTATION'),
    goal(Goal), format('Goal: '), show_term(Goal), nl,
    negated_goal(Negated), format('Negated goal: '), show_term(Negated), nl,
    transformation_stages(Stages, Clauses),
    forall(member(Name-Formulas, Stages),
           (format('~nStage: ~w~n', [Name]),
            forall(member(F, Formulas), (show_term(F), nl)))),
    writeln('No existential quantifiers: no Skolem symbols are needed.'),
    format('~nCNF CLAUSES~n'), print_clauses(Clauses, 1),
    proof(_, Trace, EmptyId), format('~nRESOLUTION TRACE~n'), maplist(print_step, Trace),
    verify_trace(Clauses, Trace, EmptyId),
    format('~nC~d = [] (empty clause). Contradiction derived.~n', [EmptyId]),
    writeln('VERIFIED: trusted(mira) follows from the knowledge base.'),
    self_test.
