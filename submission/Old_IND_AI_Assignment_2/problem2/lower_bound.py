from functools import lru_cache


class RoverLowerBound:
    def __init__(self, initial_state):
        facts = [f.strip('()').split() for f in initial_state]
        edges = [(f[1], f[2]) for f in facts if f[0] == 'connected']
        self.locations = sorted({x for edge in edges for x in edge})
        self.index = {location: i for i, location in enumerate(self.locations)}
        self.base = self.index['base']
        self.hard = {f[1] for f in facts if f[0] == 'hard'}
        self.drill_location = next(f[2] for f in facts if f[0] == 'drill-at')
        size = len(self.locations)
        self.distance = [[0 if i == j else float('inf') for j in range(size)] for i in range(size)]
        for origin, destination in edges:
            self.distance[self.index[origin]][self.index[destination]] = 1
        for k in range(size):
            for i in range(size):
                for j in range(size):
                    self.distance[i][j] = min(self.distance[i][j], self.distance[i][k] + self.distance[k][j])

    @lru_cache(maxsize=None)
    def route(self, position, mask):
        if mask == 0:
            return self.distance[position][self.base]
        return min(self.distance[position][i] + self.route(i, mask ^ (1 << i))
                   for i in range(len(self.locations)) if mask & (1 << i))

    def __call__(self, node):
        facts = [f.strip('()').split() for f in node.state]
        position = self.index[next(f[2] for f in facts if f[0] == 'at')]
        ground = [(f[1], f[2]) for f in facts if f[0] == 'rock-at' and f[2] != 'base']
        carried = [f[1] for f in facts if f[0] == 'in-bay']
        required = {location for _, location in ground}
        needs_drill = not any(f[0] == 'has-drill' for f in facts) and any(r in self.hard for r, _ in ground)
        if needs_drill:
            required.add(self.drill_location)
        mask = sum(1 << self.index[location] for location in required)
        handling = 2 * len(ground) + len(carried) + int(needs_drill)
        transport_distance = sum(self.distance[self.index[location]][self.base] for _, location in ground)
        transport_distance += len(carried) * self.distance[position][self.base]
        movement = max(self.route(position, mask), (transport_distance + 1) // 2)
        return handling + movement
