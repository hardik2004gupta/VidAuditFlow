"""Workflow Definition for VidAuditFlow's compliance audit pipeline.

Phase 3 architecture (AI_PIPELINE_VISION.md / ARCHITECTURE_EVOLUTION.md
Stage 2): a Supervisor (pure Python, no LLM) fans out to two agents that
run as true concurrent LangGraph branches, joins them, then routes linearly
through the remaining specialists:

    START
      |
      v
    supervisor_start (fan-out)
      |         |
      v         v
    transcript_agent   ocr_agent      <- run concurrently
      |         |
      v         v
    supervisor_join
      |
      +-- (transcript failed) --------------------> summary_agent
      |
      v (transcript succeeded)
    retrieval_agent
      |
      v
    compliance_agent
      |
      v
    summary_agent
      |
      v
     END

This is a plain DAG with one conditional edge for failure routing -- no
cycles, no dynamic node creation, no tool-calling agents, no
self-reflection loops. ``supervisor.route_after_join`` is LangGraph's
standard, stable ``add_conditional_edges`` mechanism, not an experimental
feature.

All nodes are ``async``, so the workflow must be run via
``await app.ainvoke(...)``, not the synchronous ``app.invoke(...)``.
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.src.graph.nodes.compliance_agent import compliance_agent
from backend.src.graph.nodes.ocr_agent import ocr_agent
from backend.src.graph.nodes.retrieval_agent import retrieval_agent
from backend.src.graph.nodes.summary_agent import summary_agent
from backend.src.graph.nodes.transcript_agent import transcript_agent
from backend.src.graph.state import VideoAuditState
from backend.src.graph.supervisor import (
    route_after_join,
    supervisor_join,
    supervisor_start,
)


def create_graph() -> CompiledStateGraph:
    """Construct and compile the LangGraph workflow.

    Returns:
        A compiled, runnable graph exposing ``ainvoke``/``astream``.
    """
    workflow = StateGraph(VideoAuditState)

    workflow.add_node("supervisor_start", supervisor_start)
    workflow.add_node("transcript_agent", transcript_agent)
    workflow.add_node("ocr_agent", ocr_agent)
    workflow.add_node("supervisor_join", supervisor_join)
    workflow.add_node("retrieval_agent", retrieval_agent)
    workflow.add_node("compliance_agent", compliance_agent)
    workflow.add_node("summary_agent", summary_agent)

    workflow.set_entry_point("supervisor_start")

    # Fan-out: both agents run in the same superstep, concurrently.
    workflow.add_edge("supervisor_start", "transcript_agent")
    workflow.add_edge("supervisor_start", "ocr_agent")

    # Join: both branches must complete before the Supervisor evaluates them.
    workflow.add_edge("transcript_agent", "supervisor_join")
    workflow.add_edge("ocr_agent", "supervisor_join")

    # Failure routing: skip Retrieval/Compliance entirely if there's no transcript.
    workflow.add_conditional_edges(
        "supervisor_join",
        route_after_join,
        {"retrieval_agent": "retrieval_agent", "summary_agent": "summary_agent"},
    )

    workflow.add_edge("retrieval_agent", "compliance_agent")
    workflow.add_edge("compliance_agent", "summary_agent")
    workflow.add_edge("summary_agent", END)

    return workflow.compile()


# Expose the runnable app for import by the API or CLI.
app = create_graph()
