"""Dummy functions used for sample pipeline."""

def start(state: dict) -> dict:
    print("Starting pipeline")
    state["message"] = "hello"
    return state

def finish(state: dict) -> dict:
    print(f"Finishing pipeline with message: {state.get('message')}")
    return state
