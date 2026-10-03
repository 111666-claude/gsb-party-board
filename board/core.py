"""组队板：每人上限、过期清理、按角色过滤与稳定排序。

缺陷：每人上限不生效、过期帖子不清理、查询不按角色过滤、结果不按时间排序、
取消不幂等、每次查询扫描全部帖子。
"""


class Board:
    """组队招募板。"""

    def __init__(self, per_player_max, ttl_ms):
        self.per_player_max = per_player_max
        self.ttl_ms = ttl_ms
        self.posts = []
        self.canceled = set()
        self.scanned = 0

    def post(self, player, roles, now_ms):
        """发布一条招募。"""
        self.scanned += len(self.posts)
        self.posts.append({"player": player, "roles": tuple(roles), "at": now_ms})
        return True

    def cancel(self, player, req_id, now_ms):
        """撤销自己的招募。"""
        self.canceled.add(req_id)
        return True

    def query(self, role, now_ms):
        """按角色查询可加入的招募。"""
        self.scanned += len(self.posts)
        return [post["player"] for post in self.posts]

    def scanned_count(self):
        return self.scanned
