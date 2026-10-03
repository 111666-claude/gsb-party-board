import unittest

from board.core import Board


def world():
    return Board(per_player_max=5, ttl_ms=100000)


class BasicTest(unittest.TestCase):
    def test_empty_query(self):
        self.assertEqual(world().query("tank", 0), [])

    def test_post_then_query(self):
        target = world()
        target.post("p1", ("tank",), 0)
        self.assertEqual(target.query("tank", 0), ["p1"])

    def test_cancel_unknown_req_returns_true(self):
        self.assertTrue(world().cancel("p1", "ghost", 0))

    def test_limits_are_stored(self):
        target = world()
        self.assertEqual((target.per_player_max, target.ttl_ms), (5, 100000))

    def test_scanned_starts_at_zero(self):
        self.assertEqual(world().scanned_count(), 0)


if __name__ == "__main__":
    unittest.main()
