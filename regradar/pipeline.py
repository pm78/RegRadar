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
        events = [
            compute_diff(res, prev)
            for res, prev in zip(state["results"], state["prevs"])
        ]
        return {"events": events}

    graph.add_node("fetch_documents", fetch_docs_node)
    graph.add_node("parse_document", parse_node)
    graph.add_node("hash_and_store", store_node)
    graph.add_node("link_versions", link_node)
    graph.add_node("compute_diff", diff_node)

    graph.add_edge("fetch_sources", "fetch_documents")
    graph.add_edge("fetch_documents", "parse_document")
    graph.add_edge("parse_document", "hash_and_store")
    graph.add_edge("hash_and_store", "link_versions")
    graph.add_edge("link_versions", "compute_diff")
    graph.add_edge("compute_diff", END)

    graph.set_entry_point("fetch_sources")
    return graph


def run() -> None:
    init_db()
    graph = build_graph()
    app = graph.compile()
    app.invoke({})


if __name__ == "__main__":
    run()
