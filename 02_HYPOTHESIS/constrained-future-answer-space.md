# Constrained Future Answer-Space

**Status:** PROVISIONAL HYPOTHESIS

A constrained future answer-space is a representation of admissible unresolved possibilities produced from explicitly identified constraints. It is not itself an assertion that any member is true.

## Necessary properties

1. **Traceability:** every constraint has a provenance chain.
2. **Non-collapse:** narrowing must not be represented as resolution unless the evidence actually establishes the answer.
3. **Revisability:** invalid constraints can reopen previously excluded possibilities.
4. **Discriminator visibility:** where possible, the system records what future information could distinguish remaining alternatives.
5. **Expectation isolation:** a preferred or predicted answer cannot silently become a constraint.
6. **Authorization separation:** narrowing alone cannot authorize action.

## Example

Evidence establishes that a future event must satisfy X or Y. The system may record `{X,Y}` as the admissible space and identify discriminator D. It must not record X or Y as resolved until D or equivalent evidence actually resolves the question.

## Falsification condition

The hypothesis should be rejected or revised if a consistent formalization cannot prevent derived narrowing from being mistaken for evidence, prediction, or resolution.
