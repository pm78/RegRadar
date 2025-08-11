"""Simple runner to execute LangGraph pipelines defined in YAML."""
import argparse
import importlib
import yaml
from langgraph.graph import StateGraph


def build_graph(config: dict):
    graph = StateGraph(dict)
    for node in config.get("nodes", []):
        name = node["name"]
        module_name, func_name = node["callable"].split(":")
        module = importlib.import_module(module_name)
        fn = getattr(module, func_name)
        graph.add_node(name, fn)
    for edge in config.get("edges", []):
        graph.add_edge(edge["source"], edge["target"])
    graph.set_entry_point(config["entry"])
    return graph.compile()


def main():
    parser = argparse.ArgumentParser(description="Run a LangGraph pipeline from YAML")
    parser.add_argument("pipeline", help="Path to the pipeline YAML file")
    args = parser.parse_args()
    with open(args.pipeline) as f:
        config = yaml.safe_load(f)
    app = build_graph(config)
    app.invoke({})


if __name__ == "__main__":
    main()
