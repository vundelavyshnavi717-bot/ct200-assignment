from typing import Any, Optional
from pydantic import BaseModel, Field

class IngestResponse(BaseModel): document_id: int; version_id: int; version: int; node_count: int
class SelectionIn(BaseModel): name: str; node_ids: list[int]
class GenerationIn(BaseModel): selection_id: int
class TestCase(BaseModel): title: str; preconditions: list[str] = []; steps: list[str]; expected_result: str; severity: str = 'medium'; source_node_ids: list[int] = []
class GenerationOut(BaseModel): id: str; status: str; stale: bool; test_cases: list[TestCase]; stale_reasons: list[str] = []
class SearchOut(BaseModel): id: int; heading: str; level: int; version_id: int; content_hash: str
