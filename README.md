# party-board

组队板：每人上限、过期清理、按角色过滤与稳定排序，只用 Python 标准库。

```
python3 -m board.cli --sample cap
python3 -m board.cli --sample ttl
python3 -m board.cli --sample filter
python3 -m board.cli --sample order
python3 -m board.cli --sample cancel
python3 -m board.cli --sample scan
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **每人上限**：同一个玩家最多同时挂 `per_player_max` 条招募，超出时
  `post` 返回 False。
- **过期**：发布超过 `ttl_ms` 的招募不再出现在查询结果里。
- **撤销**：撤销后自己的招募不再出现；同一个 `req_id` 只生效一次，
  重复撤销返回 False。
- **过滤**：`query(role)` 只返回需要该角色的招募。
- **排序**：结果按发布时间升序，时间相同按玩家 id 升序。
- **不变量**：一个玩家同时挂出的条数不超过上限；同一串发布、撤销与查询
  序列重复执行结果相同。
- **查询代价**：`query` 不许遍历全部帖子，`scanned_count`
  不随帖子总数线性增长。
- **规模**：10 万条招募、每秒 10 万次查询，单次摊还 O(命中角色的人数)。

## 输出契约（不改格式）

```
third=..
pending=..
found=..
order=..
second=..
scanned=..
```

## 目录

```
board/core.py   上限、过期、过滤与排序
board/cli.py    命令行入口
tests/          unittest 用例
```
