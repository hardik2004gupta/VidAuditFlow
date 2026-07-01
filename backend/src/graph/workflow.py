"""Workflow Definition for the Brand Guardian AI.

This module defines the Directed Acyclic Graph (DAG) that orchestrates the
video compliance audit process. It connects the nodes (functional units)
using the StateGraph primitive from LangGraph.

Architecture (unchanged from the original design -- this phase does not
redesign the graph topology, see ARCHITECTURE_EVOLUTION.md for the planned
future supervisor/multi-agent shape):

    [START] -> [index_video_node] -> [audit_content_node] -> [END]

Both nodes are ``async`` functions, so callers must invoke the compiled
graph with ``await app.ainvoke(...)`` rather than the synchronous
``app.invoke(...)``.
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.src.graph.nodes import audit_content_node, index_video_node
from backend.src.graph.state import VideoAuditState


def create_graph() -> CompiledStateGraph:
    """Construct and compile the LangGraph workflow.

    Returns:
        A compiled, runnable graph exposing ``ainvoke``/``astream``.
    """
    workflow = StateGraph(VideoAuditState)

    workflow.add_node("indexer", index_video_node)
    workflow.add_node("auditor", audit_content_node)

    workflow.set_entry_point("indexer")
    workflow.add_edge("indexer", "auditor")
    workflow.add_edge("auditor", END)

    return workflow.compile()


# Expose the runnable app for import by the API or CLI.
app = create_graph()
