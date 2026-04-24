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

    def build(self, commits: List[Dict[str, Any]], _refs: Dict[str, str] | None = None) -> None:
        """
        Build commit graph from topo-ordered commits.
        從 topo-order 的 commits 建立 commit graph。
        """
        self.nodes = [
            CommitNode(
                commit_sha=commit["sha"],
                author_name=commit["author"],
                commit_date=commit["date"],
                commit_message=commit["message"],
                parent_shas=commit["parents"],
            )
            for commit in commits
        ]
        self.index = {node.commit_sha: index for index, node in enumerate(self.nodes)}
        self._assign_lanes()

    @staticmethod
    def _pick_lane(active: Dict[int, str], free_lanes: List[int], sha: str) -> int:
        """選出 commit 應該配置的 lane / Pick the lane for this commit."""
        for lane, lane_sha in active.items():
            if lane_sha == sha:
                return lane
        if free_lanes:
            return free_lanes.pop(0)
        return 0 if not active else max(active.keys()) + 1

    @staticmethod
    def _assign_parent_lanes(active: Dict[int, str], free_lanes: List[int],
                             node_lane: int, parent_shas: List[str]) -> None:
        """把父節點放進 active lanes / Assign each parent to a lane in-place."""
        if not parent_shas:
            return
        active[node_lane] = parent_shas[0]
        for parent in parent_shas[1:]:
            lane = free_lanes.pop(0) if free_lanes else (max(active.keys()) + 1)
            active[lane] = parent

    @staticmethod
    def _recompute_free_lanes(active: Dict[int, str], free_lanes: List[int]) -> List[int]:
        """回傳更新後的 free lane 清單 / Return updated free lane list."""
        if not active:
            return free_lanes
        max_lane = max(active.keys())
        used = set(active.keys())
        all_lanes = set(range(max_lane + 1))
        return sorted(set(free_lanes).union(all_lanes - used))

    def _assign_lanes(self) -> None:
        """分配 lanes，模擬 `git log --graph` / Assign lanes to commits, like `git log --graph`."""
        active: Dict[int, str] = {}
        free_lanes: List[int] = []
        for node in self.nodes:
            node.lane_index = self._pick_lane(active, free_lanes, node.commit_sha)
            active = {lane: sha for lane, sha in active.items() if sha != node.commit_sha}
            self._assign_parent_lanes(active, free_lanes, node.lane_index, node.parent_shas)
            free_lanes = self._recompute_free_lanes(active, free_lanes)
