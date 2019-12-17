from graphsets import Graphset

def validate_graphset(graphset):
    if isinstance(graphset, Graphset):
        return graphset
    elif isinstance(graphset, type) and issubclass(graphset, Graphset):
        return graphset()
    else:
        raise ValueError("Must be a Graphset class or instance")

def make_test_ticks():
    pass

def make_poll_results():
    pass
