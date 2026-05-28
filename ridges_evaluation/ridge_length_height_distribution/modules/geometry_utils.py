from typing import List, Tuple, Dict, Any

import numpy as np
from shapely.geometry import Point
from shapely.strtree import STRtree

class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


def get_endpoints(geom):
    if geom.geom_type == "LineString":
        coords = list(geom.coords)
        if len(coords) < 2:
            raise ValueError("LineString has fewer than 2 coordinates.")
        return Point(coords[0]), Point(coords[-1])

    if geom.geom_type == "MultiLineString":
        parts = list(geom.geoms)
        if not parts:
            raise ValueError("MultiLineString has no parts.")
        first_coords = list(parts[0].coords)
        last_coords = list(parts[-1].coords)
        if len(first_coords) < 2 or len(last_coords) < 2:
            raise ValueError("MultiLineString contains a degenerate part.")
        return Point(first_coords[0]), Point(last_coords[-1])

    raise ValueError(f"Unsupported geometry type: {geom.geom_type}")


def assign_ridge_ids(records: List[Dict[str, Any]], tolerance: float) -> List[int]:
    n = len(records)
    uf = UnionFind(n)

    endpoint_records: List[Tuple[int, str, Point]] = []
    endpoint_points: List[Point] = []

    for i, rec in enumerate(records):
        p0, p1 = get_endpoints(rec["geometry"])
        endpoint_records.append((i, "start", p0))
        endpoint_records.append((i, "end", p1))
        endpoint_points.extend([p0, p1])

    tree = STRtree(endpoint_points)

    geom_id_to_epidx = None
    if endpoint_points:
        geom_id_to_epidx = {id(g): idx for idx, g in enumerate(endpoint_points)}

    for _, (seg_i, _, pt_i) in enumerate(endpoint_records):
        query_env = pt_i.buffer(tolerance).envelope
        cand = tree.query(query_env)

        if len(cand) == 0:
            continue

        if isinstance(cand[0], (int, np.integer)):
            candidate_ep_indices = cand.tolist()
        else:
            candidate_ep_indices = []
            for g in cand:
                idx = geom_id_to_epidx.get(id(g))
                if idx is not None:
                    candidate_ep_indices.append(idx)

        for j in candidate_ep_indices:
            seg_j, _, pt_j = endpoint_records[j]

            if seg_i >= seg_j:
                continue

            if pt_i.distance(pt_j) <= tolerance:
                uf.union(seg_i, seg_j)

    root_to_ridge_id = {}
    next_id = 1
    ridge_ids = []

    for i in range(n):
        root = uf.find(i)
        if root not in root_to_ridge_id:
            root_to_ridge_id[root] = next_id
            next_id += 1
        ridge_ids.append(root_to_ridge_id[root])

    return ridge_ids