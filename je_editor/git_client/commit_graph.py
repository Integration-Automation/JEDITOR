import logging
from dataclasses import dataclass, field
from typing import List, Dict

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

    def build(self, commits: List[Dict], refs: Dict[str, str]) -> None:
        # commits are topo-ordered by git_client log --topo-order; we keep it.
        self.nodes = [
            CommitNode(
                commit_sha=c["sha"],
                author_name=c["author"],
                commit_date=c["date"],
                commit_message=c["message"],
                parent_shas=c["parents"],
            ) for c in commits
        ]
        self.index = {n.commit_sha: i for i, n in enumerate(self.nodes)}
        self._assign_lanes()

    def _assign_lanes(self) -> None:
        """
        Simple lane assignment similar to 'git_client log --graph' lanes.
        Greedy: reuse freed lanes; parents may create new lanes.
        """
        active: Dict[int, str] = {}  # lane -> sha
        free_lanes: List[int] = []

        for i, node in enumerate(self.nodes):
            # If any active lane points to this commit, use that lane
            lane_found = None
            for lane, sha in list(active.items()):
                if sha == node.commit_sha:
                    lane_found = lane
                    break

            if lane_found is None:
                if free_lanes:
                    node.lane_index = free_lanes.pop(0)
                else:
                    node.lane_index = 0 if not active else max(active.keys()) + 1
            else:
                node.lane_index = lane_found

            # Update active: current node consumes its lane, parents occupy lanes
            # Remove the current sha from any lane that pointed to it
            for lane, sha in list(active.items()):
                if sha == node.commit_sha:
                    del active[lane]

            # First parent continues in the same lane; others go to free/new lanes
            if node.parent_shas:
                first = node.parent_shas[0]
                active[node.lane_index] = first
                # Side branches
                for p in node.parent_shas[1:]:
                    # Pick a free lane or new one
                    if free_lanes:
                        pl = free_lanes.pop(0)
                    else:
                        pl = 0 if not active else max(active.keys()) + 1
                    active[pl] = p

            # Any lane whose target no longer appears in the future will be freed later
            # We approximate by freeing lanes when a target didn't appear in the next rows;
            # but for minimal viable, free when lane not reassigned by parents this row.
            used_lanes = set(active.keys())
            # Collect gaps below max lane as free lanes to reuse
            max_lane = max(used_lanes) if used_lanes else -1
            present = set(range(max_lane + 1))
            missing = sorted(list(present - used_lanes))
            # Merge missing into free_lanes maintaining order
            free_lanes = sorted(set(free_lanes + missing))
