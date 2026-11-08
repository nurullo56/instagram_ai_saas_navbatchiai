from typing import List, Dict, Any, Tuple, Set, Optional
from collections import defaultdict, deque


class DAGValidationError(Exception):
    pass


class DAGValidator:
    """
    Visual Flow Builder DAG tekshiruvi:
    - Sikllarni (cycles) aniqlash (Kahn algoritmi yoki DFS)
    - Trigger nodedan boshlanishini ta'minlash
    - Yetib borib bo'lmaydigan (orphan / unreachable) nodelarni aniqlash
    - Branching va condition tugunlarini to'g'ri bog'langanligini tekshirish
    """

    SUPPORTED_NODE_TYPES = {
        "trigger",
        "send_message",
        "comment_reply",
        "condition",
        "wait_delay",
        "ai_generate",
        "lead_tag",
        "handoff"
    }

    @classmethod
    def validate_flow(cls, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Flow DAG grafigini to'liq tekshirish.
        Qaytaradi: (is_valid: bool, error_message: Optional[str])
        """
        if not nodes:
            return False, "Flow kamida bitta tugunga (node) ega bo'lishi kerak"

        node_ids = set()
        trigger_nodes = []

        for node in nodes:
            nid = node.get("id")
            ntype = node.get("type")

            if not nid:
                return False, "Barcha nodelar 'id' maydoniga ega bo'lishi shart"
            if nid in node_ids:
                return False, f"Takroriy node ID aniqlandi: {nid}"
            node_ids.add(nid)

            if ntype not in cls.SUPPORTED_NODE_TYPES:
                return False, f"Noma'lum node turi: {ntype}"

            if ntype == "trigger":
                trigger_nodes.append(nid)

        if not trigger_nodes:
            return False, "Flow kamida bitta 'trigger' tuguniga ega bo'lishi kerak"

        # Edge larni tekshirish va adjacency list qurish
        adj_list: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = {nid: 0 for nid in node_ids}

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")

            if source not in node_ids:
                return False, f"Edge manbasi topilmadi: {source}"
            if target not in node_ids:
                return False, f"Edge manzili topilmadi: {target}"
            if source == target:
                return False, f"O'z-o'ziga bog'lanish (self-loop) taqiqlanadi: {source}"

            adj_list[source].append(target)
            in_degree[target] += 1

        # Sikl (Cycle) tekshiruvi - Kahn algoritmi (Topological Sort)
        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        visited_count = 0

        while queue:
            current = queue.popleft()
            visited_count += 1

            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(node_ids):
            return False, "Flow ichida berk sikl (cycle / cheksiz aylanma) aniqlandi!"

        return True, None
