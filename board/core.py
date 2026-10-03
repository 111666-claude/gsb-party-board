"""组队板：每人上限、过期清理、按角色过滤与稳定排序。

实现要点：
- 每个角色维护一个按 (发布时间, 玩家 id, 帖子 id) 升序的跳表，query 只遍历
  命中角色的结果，摊还代价 O(命中人数)，不随帖子总数线性增长。
- 过期帖子通过全局小顶堆惰性清理；被清理或撤销的索引节点标记为墓碑，
  在查询遍历时摘除并计入 scanned（摊还 O(1)）。
- 撤销按 req_id 幂等：同一个 req_id 只生效一次，重复撤销返回 False。
"""

import heapq
import random

_MAX_LEVEL = 32
_BRANCHING = 4


class _Node:
    __slots__ = ("key", "next")

    def __init__(self, key, level):
        self.key = key
        self.next = [None] * level


class _SkipList:
    """按键升序的跳表，支持插入、删除与从头顺序遍历。"""

    def __init__(self, rng):
        self._rng = rng
        self._head = _Node(None, _MAX_LEVEL)

    def _random_level(self):
        level = 1
        while level < _MAX_LEVEL and self._rng.randrange(_BRANCHING) == 0:
            level += 1
        return level

    def add(self, key):
        update = [self._head] * _MAX_LEVEL
        node = self._head
        for level in range(_MAX_LEVEL - 1, -1, -1):
            while node.next[level] is not None and node.next[level].key < key:
                node = node.next[level]
            update[level] = node
        node = _Node(key, self._random_level())
        for level in range(len(node.next)):
            node.next[level] = update[level].next[level]
            update[level].next[level] = node

    def discard(self, key):
        node = self._head
        for level in range(_MAX_LEVEL - 1, -1, -1):
            while node.next[level] is not None and node.next[level].key < key:
                node = node.next[level]
            target = node.next[level]
            if target is not None and target.key == key:
                node.next[level] = target.next[level]

    def head(self):
        return self._head.next[0]


class Board:
    """组队招募板。"""

    def __init__(self, per_player_max, ttl_ms):
        self.per_player_max = per_player_max
        self.ttl_ms = ttl_ms
        self._rng = random.Random(0)
        self._posts = {}            # post_id -> (player, roles, at)
        self._role_index = {}       # role -> _SkipList，键 (at, player, post_id)
        self._expiry = []           # (at, post_id) 小顶堆
        self._active = {}           # player -> 未过期未撤销的帖子数
        self._used_req_ids = set()
        self._dead = set()          # 已失效但索引节点尚未摘除的 post_id
        self._next_id = 0
        self.scanned = 0

    def post(self, player, roles, now_ms):
        """发布一条招募；超过每人上限时返回 False。"""
        self._purge_expired(now_ms)
        if self._active.get(player, 0) >= self.per_player_max:
            return False
        post_id = self._next_id
        self._next_id += 1
        roles = tuple(roles)
        self._posts[post_id] = (player, roles, now_ms)
        key = (now_ms, player, post_id)
        for role in set(roles):
            index = self._role_index.get(role)
            if index is None:
                index = self._role_index[role] = _SkipList(self._rng)
            index.add(key)
        heapq.heappush(self._expiry, (now_ms, post_id))
        self._active[player] = self._active.get(player, 0) + 1
        self.scanned += 1
        return True

    def cancel(self, player, req_id, now_ms):
        """撤销自己的招募；同一个 req_id 只生效一次。"""
        if req_id in self._used_req_ids:
            return False
        self._used_req_ids.add(req_id)
        self._purge_expired(now_ms)
        for post_id, (owner, _roles, _at) in list(self._posts.items()):
            if owner == player:
                self._kill(post_id)
        return True

    def query(self, role, now_ms):
        """按角色查询可加入的招募，按 (发布时间, 玩家 id) 升序。"""
        self._purge_expired(now_ms)
        index = self._role_index.get(role)
        if index is None:
            return []
        found = []
        node = index.head()
        while node is not None:
            _at, player, post_id = node.key
            if post_id in self._dead:
                self.scanned += 1
                index.discard(node.key)
            else:
                found.append(player)
            node = node.next[0]
        return found

    def scanned_count(self):
        return self.scanned

    def _kill(self, post_id):
        player, _roles, _at = self._posts.pop(post_id)
        self._active[player] -= 1
        if self._active[player] <= 0:
            del self._active[player]
        self._dead.add(post_id)
        self.scanned += 1

    def _purge_expired(self, now_ms):
        while self._expiry and now_ms - self._expiry[0][0] > self.ttl_ms:
            _at, post_id = heapq.heappop(self._expiry)
            if post_id in self._posts:
                self._kill(post_id)
