from __future__ import annotations

from langgraph.graph import END, StateGraph

from .database import init_db
from .nodes import (
    compute_diff,
    fetch_documents,
    fetch_sources,
    hash_and_store,
    link_versions,
    parse_document,
    classify,
    summarize_impact,
    guard_citations,
    score_priority,
    publish,
    human_review,
)


def build_graph() -> StateGraph:
    graph = StateGraph(dict)
    graph.add_node("fetch_sources", lambda state: {"sources": fetch_sources()})

    def fetch_docs_node(state):
        docs = fetch_documents(state["sources"])
        return {"raw_docs": docs}

    def parse_node(state):
        parsed = [parse_document(doc) for doc in state["raw_docs"]]
        return {"parsed_docs": parsed}

    def store_node(state):
        results = [hash_and_store(doc) for doc in state["parsed_docs"]]
        return {"results": results}

    def link_node(state):
        prevs = [link_versions(res) for res in state["results"]]
        return {"prevs": prevs}

    def diff_node(state):
        for res, prev in zip(state["results"], state["prevs"]):
            event = compute_diff(res, prev)
            if event is not None:
                return {"event": event, "result": res}
        return {}

    def classify_node(state):
        if "event" not in state:
            return {}
        return {"classification": classify(state["event"].diff)}

    def summarize_node(state):
        if "event" not in state:
            return {}
        text = state["result"].version.content
        return {"summary": summarize_impact(text)}

    def guard_node(state):
        if "event" not in state:
            return {}
        text = state["result"].version.content
        return {"guard": guard_citations(text, state["summary"])}

    def score_node(state):
        if "classification" not in state:
            return {}
        return {"score": score_priority(state["classification"])}

    def publish_node(state):
        if "event" not in state:
            return {}
        publish(state["result"], state["summary"], state["score"])
        return {}

    def review_node(state):
        return human_review(state)

    def qc_gate(state):
        if "event" not in state:
            return "human_review"
        if not state["guard"].get("guard_passed"):
            return "human_review"
        if state["classification"].get("confidence", 0) < 0.7:
            return "human_review"
        return "publish"

    graph.add_node("fetch_documents", fetch_docs_node)
    graph.add_node("parse_document", parse_node)
    graph.add_node("hash_and_store", store_node)
    graph.add_node("link_versions", link_node)
    graph.add_node("compute_diff", diff_node)
    graph.add_node("classify", classify_node)
    graph.add_node("summarize_impact", summarize_node)
    graph.add_node("guard_citations", guard_node)
    graph.add_node("score_priority", score_node)
    graph.add_node("publish", publish_node)
    graph.add_node("human_review", review_node)

    graph.add_edge("fetch_sources", "fetch_documents")
    graph.add_edge("fetch_documents", "parse_document")
    graph.add_edge("parse_document", "hash_and_store")
    graph.add_edge("hash_and_store", "link_versions")
    graph.add_edge("link_versions", "compute_diff")
    graph.add_edge("compute_diff", "classify")
    graph.add_edge("compute_diff", "summarize_impact")
    graph.add_edge("classify", "score_priority")
    graph.add_edge("summarize_impact", "guard_citations")
    graph.add_edge("score_priority", "qc_gate")
    graph.add_edge("guard_citations", "qc_gate")
    graph.add_conditional_edges("qc_gate", qc_gate, {"publish": "publish", "human_review": "human_review"})
    graph.add_edge("publish", END)
    graph.add_edge("human_review", END)

    graph.set_entry_point("fetch_sources")
    return graph


def run() -> None:
    init_db()
    graph = build_graph()
    app = graph.compile()
    app.invoke({})


if __name__ == "__main__":
    run()
