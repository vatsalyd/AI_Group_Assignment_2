# Problem 3: Royal archive access verification

## 1. Knowledge representation

Constants are `mira`, `scroll_7`, and `royal_archive`. Variables x,y denote
people or records as appropriate in this single-sorted FOL encoding.

| Predicate | Meaning |
| --- | --- |
| Archivist(x) | x is an archivist |
| Verifies(x,r) | x verifies record r |
| Trusted(x) | x is trusted |
| Access(x,r) | x has access to r |
| Sealed(r) | r is sealed |
| Permitted(x,r) | x may inspect r |
| Inspects(x,r) | x actually inspects r |
| FindsMark(x,r) | x finds a hidden mark in r |
| Stored(r,a) | r is stored in archive a |

The formulas are:

1. `forall x,r: (Archivist(x) and Verifies(x,r)) -> Trusted(x)`.
2. `forall x,r: (Trusted(x) and Access(x,r) and Sealed(r)) -> Permitted(x,r)`.
3. `forall x,r: (Inspects(x,r) and FindsMark(x,r)) -> Verifies(x,r)`.
4. `forall r: Stored(r,royal_archive) -> Sealed(r)`.
5. `Stored(scroll_7,royal_archive)`.
6. `Access(mira,scroll_7)`.
7. `Inspects(mira,scroll_7) and FindsMark(mira,scroll_7)`.
8. `Archivist(mira)`.

`Permitted` and `Inspects` are different predicates. Permission does not
imply that an inspection actually occurred.

## 2. Negate the goal

The goal is `Trusted(mira)`. Add `not Trusted(mira)` to the knowledge base.
The program does not add the positive goal as a fact.

## 3. Conversion to clause form

The program represents formulas as terms and performs each transformation.
Implications become `not antecedent or consequent`. De Morgan's laws move
negations to predicates. For example, the first rule becomes

`forall x,r: not Archivist(x) or not Verifies(x,r) or Trusted(x)`.

Bound variables are renamed freshly for each scope. Clauses use distinct
variables across rules, and each resolution parent is copied separately
to standardize variables apart again. Variables printed as A,B in different
clauses are local to their clauses, not shared across them.

There are no existential quantifiers, so Skolemization introduces no new
symbols. Universal quantifiers are omitted in clause form. Disjunction is
distributed over conjunction when needed; the conjunction of the two
ground facts in formula 7 produces two unit clauses.

All variables in the following clauses are universally quantified:

| Clause | Literals |
| --- | --- |
| C1 | not Archivist(x1) or not Verifies(x1,r1) or Trusted(x1) |
| C2 | not Trusted(x2) or not Access(x2,r2) or not Sealed(r2) or Permitted(x2,r2) |
| C3 | not Inspects(x3,r3) or not FindsMark(x3,r3) or Verifies(x3,r3) |
| C4 | not Stored(r4,royal_archive) or Sealed(r4) |
| C5 | Stored(scroll_7,royal_archive) |
| C6 | Access(mira,scroll_7) |
| C7 | Inspects(mira,scroll_7) |
| C8 | FindsMark(mira,scroll_7) |
| C9 | Archivist(mira) |
| C10 | not Trusted(mira) |

## 4. Prolog implementation

`royal_archive_access.pl` contains the required eight labeled sections.
`main/0` prints the formulas, transformation stages, clauses, and proof.
`resolve/5` selects complementary literals, performs unification with an
occurs check, and returns the remaining literals. Set-of-support resolution
starts from the negated goal and prefers shorter new resolvents. This is a
procedure for the supplied knowledge base, not a claim of a complete
general-purpose first-order theorem prover.

## 5. Resolution refutation

The executed proof produces the following resolvents in order. Clause
variables are renamed below for readability; literal order is immaterial.

| New clause | Parents | Unification | Resolvent |
| --- | --- | --- | --- |
| C11 | C1, C10 | x1=mira | not Archivist(mira) or not Verifies(mira,r1) |
| C12 | C9, C11 | ground Archivist literal | not Verifies(mira,r1) |
| C13 | C3, C12 | x3=mira, r3=r1 | not Inspects(mira,r1) or not FindsMark(mira,r1) |
| C14 | C7, C13 | r1=scroll_7 | not FindsMark(mira,scroll_7) |
| C15 | C8, C14 | identical ground mark literals | [] |

C15 is the empty clause, a contradiction. Therefore the original knowledge
base entails `Trusted(mira)`. The substantive chain is that the observed
inspection and mark establish verification, and verification plus archivist
status establish trust. Rules about sealing, access and permission are not
needed for this conclusion.

## 6. Proof verification

The saved `outputs/proof_output.txt` is actual SWI-Prolog output. It ends
with `C15 = []`, the verified conclusion, and a passing self-test message.
The program replays every recorded resolution step against its parents.
Self-tests check preservation of repeated variables in CNF, ordinary and
occurs-check unification, absence of an assumed positive goal, and failure
to refute after separately removing the inspection, mark, or archivist fact.

Run manually from the repository root:

```powershell
swipl -q -s problem3/royal_archive_access.pl -g main -t halt
```

Use `screenshots/README.md` to capture genuine execution screenshots.

## Runtime reference

[SWI-Prolog downloads](https://www.swi-prolog.org/download/stable) provides
the runtime. The verified run used SWI-Prolog version 10.0.2 for x64-win64.
