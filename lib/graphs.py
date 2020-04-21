class HasCyclesError(Exception): pass

def topological_sort(graph):
    result = []
    done = set()
    def scan(node):
        if node in cur:
            raise HasCyclesError()
        cur.add(node)
        if node not in done:
            done.add(node)
            for link in graph[node]:
                scan(link)
            result.append(node)
        cur.remove(node)
    for node in graph.keys():
        cur = set()
        scan(node)
    return result
def has_cycles(graph):
    try:
        topological_sort(graph)
    except HasCyclesError:
        return True
    else:
        return False
