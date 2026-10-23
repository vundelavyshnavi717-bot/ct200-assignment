import json, os, uuid
from .schemas import TestCase

PROMPT_VERSION = 'v1'

def _deterministic_cases(text: str, node_ids: list[int]) -> list[dict]:
    # Safe offline fallback: useful for demos and tests; production can replace this adapter.
    focus = text[:160].replace('\n', ' ')
    return [
      {'title':'Verify documented behavior','preconditions':['Device is ready for use'], 'steps':[f'Exercise the behavior described by: {focus}'], 'expected_result':'Observed behavior matches the selected manual text.', 'severity':'medium','source_node_ids':node_ids},
      {'title':'Verify boundary condition','preconditions':['Test setup is controlled'], 'steps':['Apply the documented lower and upper boundary conditions.'], 'expected_result':'Boundary handling matches the stated limits and does not produce unsafe behavior.', 'severity':'high','source_node_ids':node_ids},
      {'title':'Verify recovery or error handling','preconditions':['A repeatable fault can be introduced'], 'steps':['Introduce the relevant fault and observe the device response.'], 'expected_result':'The documented error, recovery action, and user-visible result occur.', 'severity':'high','source_node_ids':node_ids}
    ]

def generate(text: str, node_ids: list[int]) -> list[dict]:
    # Provider hook intentionally omitted: validate any external response against TestCase before persistence.
    return [TestCase.model_validate(x).model_dump() for x in _deterministic_cases(text, node_ids)]
