from __future__ import annotations

from dataclasses import dataclass
from graphlib import TopologicalSorter
import json
import logging
from pathlib import Path
import re
from time import perf_counter
from typing import Any, Callable

OpFn = Callable[[dict[str, Any], dict[str, str]], dict[str, Any] | None]


@dataclass(frozen=True)
class PipelineNode:
    node_id: str
    attrs: dict[str, str]


@dataclass(frozen=True)
class DotPipeline:
    name: str
    nodes: dict[str, PipelineNode]
    edges: list[tuple[str, str]]


_NODE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\[(.+)\]\s*;$")
_EDGE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*->\s*([A-Za-z_][A-Za-z0-9_]*)\s*;$")
_DIGRAPH_RE = re.compile(r"^digraph\s+([A-Za-z_][A-Za-z0-9_]*)\s*{$")
_ATTR_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*("[^"]*"|[^,]+)')


def _parse_attrs(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for key, value in _ATTR_RE.findall(raw):
        clean = value.strip().strip('"')
        attrs[key] = clean
    return attrs


def parse_dot(text: str) -> DotPipeline:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("//")]
    if not lines:
        raise ValueError("DOT content is empty")

    header = lines[0]
    match = _DIGRAPH_RE.match(header)
    if not match:
        raise ValueError("DOT must start with 'digraph <name> {'")
    name = match.group(1)

    if lines[-1] != "}":
        raise ValueError("DOT must end with '}'")

    nodes: dict[str, PipelineNode] = {}
    edges: list[tuple[str, str]] = []

    for line in lines[1:-1]:
        node_match = _NODE_RE.match(line)
        if node_match:
            node_id = node_match.group(1)
            attrs = _parse_attrs(node_match.group(2))
            nodes[node_id] = PipelineNode(node_id=node_id, attrs=attrs)
            continue

        edge_match = _EDGE_RE.match(line)
        if edge_match:
            source, target = edge_match.group(1), edge_match.group(2)
            edges.append((source, target))
            if source not in nodes:
                nodes[source] = PipelineNode(node_id=source, attrs={})
            if target not in nodes:
                nodes[target] = PipelineNode(node_id=target, attrs={})
            continue

        raise ValueError(f"Unsupported DOT line: {line}")

    return DotPipeline(name=name, nodes=nodes, edges=edges)


def load_dot(path: str | Path) -> DotPipeline:
    dot_path = Path(path)
    return parse_dot(dot_path.read_text(encoding="utf-8"))


def _topological_order(pipeline: DotPipeline) -> list[str]:
    dep_map: dict[str, set[str]] = {node_id: set() for node_id in pipeline.nodes}
    for source, target in pipeline.edges:
        dep_map[target].add(source)

    sorter = TopologicalSorter(dep_map)
    return list(sorter.static_order())


def run_pipeline(
    pipeline: DotPipeline,
    registry: dict[str, OpFn],
    context: dict[str, Any] | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    ctx: dict[str, Any] = dict(context or {})
    trace: list[dict[str, Any]] = list(ctx.get("_trace", []))
    run_start = perf_counter()

    log = logger or logging.getLogger("synexis.pipeline")
    order = _topological_order(pipeline)

    for node_id in order:
        node = pipeline.nodes[node_id]
        op_name = node.attrs.get("op", node_id)
        if op_name not in registry:
            raise KeyError(f"Operation '{op_name}' is not registered")

        op_start = perf_counter()
        result = registry[op_name](ctx, node.attrs)
        if result is not None:
            if not isinstance(result, dict):
                raise TypeError(f"Operation '{op_name}' must return dict or None")
            ctx.update(result)
        op_ms = round((perf_counter() - op_start) * 1000.0, 3)

        trace_item = {
            "node": node_id,
            "op": op_name,
            "duration_ms": op_ms,
        }
        trace.append(trace_item)
        log.info(json.dumps({"event": "pipeline.node", "pipeline": pipeline.name, **trace_item}, sort_keys=True))

    total_ms = round((perf_counter() - run_start) * 1000.0, 3)
    ctx["_trace"] = trace
    ctx["_stats"] = {
        "pipeline": pipeline.name,
        "nodes_total": len(order),
        "nodes_executed": len(trace),
        "duration_ms": total_ms,
    }
    return ctx


def run_dot_file(
    path: str | Path,
    registry: dict[str, OpFn],
    context: dict[str, Any] | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    pipeline = load_dot(path)
    return run_pipeline(pipeline=pipeline, registry=registry, context=context, logger=logger)
