"""Small local trace recorder for deterministic workflow steps."""

import time
from typing import Any, Callable, Dict, List, Optional

from .schemas import ToolTraceEntry


class TraceRecorder:
    def __init__(self) -> None:
        self.entries: List[ToolTraceEntry] = []

    def run(
        self,
        tool_name: str,
        requirement_ids: List[str],
        inputs: Dict[str, Any],
        fn: Callable[..., Any],
        evidence_ids: Optional[List[str]] = None,
        output_summary: Optional[Callable[[Any], Dict[str, Any]]] = None,
        evidence_id_extractor: Optional[Callable[[Any], List[str]]] = None,
    ) -> Any:
        started = time.perf_counter()
        collected_evidence_ids = evidence_ids or []
        try:
            result = fn()
            status = "ok"
            outputs = output_summary(result) if output_summary else _summarize(result)
            if evidence_id_extractor:
                collected_evidence_ids = evidence_id_extractor(result)
            return result
        except Exception as exc:
            status = "error"
            outputs = {"error": str(exc)}
            raise
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 3)
            self.entries.append(
                ToolTraceEntry(
                    tool_name=tool_name,
                    status=status,
                    inputs=inputs,
                    outputs=outputs,
                    duration_ms=duration_ms,
                    requirement_ids=requirement_ids,
                    evidence_ids=collected_evidence_ids,
                )
            )


def _summarize(value: Any) -> Dict[str, Any]:
    if isinstance(value, tuple):
        return {"items": len(value)}
    if isinstance(value, list):
        return {"count": len(value)}
    if isinstance(value, dict):
        return {"keys": sorted(value.keys())}
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return {
            key: dumped[key]
            for key in dumped
            if key not in {"line_items", "evidence_ids", "rationale"}
        }
    return {"value": str(value)}
