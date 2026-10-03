"""组队板：每人上限、过期清理、按角色过滤与稳定排序。

实现：按角色分桶的有序索引（发布时间升序、玩家 id 升序），撤销走懒删除，
查询只命中目标角色的桶并跳过过期前缀，不遍历全部帖子。
"""

from bisect import bisect_left, insort


class Board:
    """组队招募板。"""

    def __init__(self, per_player_max, ttl_ms):
        self.per_player_max = per_player_max
        self.ttl_ms = ttl_ms
        self.by_role = {}
        self.live = {}
        self.alive = set()
        self.canceled = set()
        self.player_counts = {}
        self.next_seq = 0
        self.scanned = 0

    def post(self, player, roles, now_ms):
        """发布一条招募；同一玩家超过 per_player_max 条时返回 False。"""
        count = self.player_counts.get(player, 0)
        if count >= self.per_player_max:
            return False
        seq = self.next_seq
        self.next_seq += 1
        self.alive.add(seq)
        entry = (now_ms, player, seq)
        for role in frozenset(roles):
            insort(self.by_role.setdefault(role, []), entry)
        self.live.setdefault(player, []).append(seq)
        self.player_counts[player] = count + 1
        return True

    def cancel(self, player, req_id, now_ms):
        """撤销自己的招募；同一个 req_id 只生效一次，重复撤销返回 False。"""
        if req_id in self.canceled:
            return False
        self.canceled.add(req_id)
        for seq in self.live.pop(player, ()):
            self.alive.discard(seq)
        self.player_counts[player] = 0
        return True

    def query(self, role, now_ms):
        """按角色查询可加入的招募，按发布时间升序、时间相同按玩家 id 升序。"""
        entries = self.by_role.get(role)
        if not entries:
            return []
        cutoff = now_ms - self.ttl_ms
        start = bisect_left(entries, (cutoff,))
        result = []
        for index in range(start, len(entries)):
            at, player, seq = entries[index]
            if seq in self.alive:
                result.append(player)
            else:
                self.scanned += 1
        return result

    def scanned_count(self):
        return self.scanned
