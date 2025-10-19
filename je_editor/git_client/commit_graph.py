import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

log = logging.getLogger(__name__)


@dataclass
class CommitNode:
    commit_sha: str
    author_name: str
    commit_date: str
    commit_message: str
    parent_shas: List[str]
    lane_index: int = -1  # assigned later


@dataclass
class CommitGraph:
    nodes: List[CommitNode] = field(default_factory=list)
    index: Dict[str, int] = field(default_factory=dict)  # sha -> row

    def build(self, commits: List[Dict[str, Any]], refs: Dict[str, str] | None = None) -> None:
        """
        Build commit graph from topo-ordered commits.
        從 topo-order 的 commits 建立 commit graph。
        """
        self.nodes = [
            CommitNode(
                commit_sha=c["sha"],
                author_name=c["author"],
                commit_date=c["date"],
                commit_message=c["message"],
                parent_shas=c["parents"],
            )
            for c in commits
        ]
        self.index = {n.commit_sha: i for i, n in enumerate(self.nodes)}
        self._assign_lanes()

    def _assign_lanes(self) -> None:
        """
        Assign lanes to commits, similar to `git log --graph`.
        分配 lanes，模擬 `git log --graph` 的效果。
        """
        active: Dict[int, str] = {}  # lane -> sha
        free_lanes: List[int] = []

        for node in self.nodes:
            # Step 1: 找到 lane
            lane_found = next((lane for lane, sha in active.items() if sha == node.commit_sha), None)

            if lane_found is not None:
                node.lane_index = lane_found
            elif free_lanes:
                node.lane_index = free_lanes.pop(0)
            else:
                node.lane_index = 0 if not active else max(active.keys()) + 1

            # Step 2: 更新 active
            # 移除舊的 sha
            active = {lane: sha for lane, sha in active.items() if sha != node.commit_sha}

            # 父節點分配 lane
            if node.parent_shas:
                first_parent = node.parent_shas[0]
                active[node.lane_index] = first_parent
                for p in node.parent_shas[1:]:
                    pl = free_lanes.pop(0) if free_lanes else (max(active.keys()) + 1)
                    active[pl] = p

            # Step 3: 更新 free_lanes
            if active:
                max_lane = max(active.keys())
                used = set(active.keys())
                all_lanes = set(range(max_lane + 1))
                free_lanes = sorted(set(free_lanes).union(all_lanes - used))
