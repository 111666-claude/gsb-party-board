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


class CapTest(unittest.TestCase):
    def test_over_limit_post_returns_false(self):
        target = Board(per_player_max=2, ttl_ms=100000)
        self.assertTrue(target.post("p1", ("tank",), 0))
        self.assertTrue(target.post("p1", ("tank",), 1))
        self.assertFalse(target.post("p1", ("tank",), 2))

    def test_cap_is_per_player(self):
        target = Board(per_player_max=1, ttl_ms=100000)
        self.assertTrue(target.post("p1", ("tank",), 0))
        self.assertTrue(target.post("p2", ("tank",), 0))
        self.assertFalse(target.post("p1", ("tank",), 1))

    def test_rejected_post_not_visible(self):
        target = Board(per_player_max=1, ttl_ms=100000)
        target.post("p1", ("tank",), 0)
        target.post("p1", ("healer",), 1)
        self.assertEqual(target.query("healer", 2), [])


class TtlTest(unittest.TestCase):
    def test_expired_post_hidden(self):
        target = Board(per_player_max=5, ttl_ms=1000)
        target.post("p1", ("tank",), 0)
        self.assertEqual(target.query("tank", 1001), [])

    def test_post_at_boundary_still_visible(self):
        target = Board(per_player_max=5, ttl_ms=1000)
        target.post("p1", ("tank",), 0)
        self.assertEqual(target.query("tank", 1000), ["p1"])


class FilterTest(unittest.TestCase):
    def test_query_returns_only_matching_role(self):
        target = world()
        target.post("p1", ("tank",), 0)
        target.post("p2", ("healer",), 1)
        self.assertEqual(target.query("tank", 10), ["p1"])
        self.assertEqual(target.query("healer", 10), ["p2"])

    def test_multi_role_post_found_by_each_role(self):
        target = world()
        target.post("p1", ("tank", "healer"), 0)
        self.assertEqual(target.query("tank", 0), ["p1"])
        self.assertEqual(target.query("healer", 0), ["p1"])


class OrderTest(unittest.TestCase):
    def test_sorted_by_publish_time(self):
        target = world()
        target.post("p2", ("tank",), 20)
        target.post("p1", ("tank",), 10)
        self.assertEqual(target.query("tank", 30), ["p1", "p2"])

    def test_same_time_sorted_by_player_id(self):
        target = world()
        target.post("p2", ("tank",), 10)
        target.post("p1", ("tank",), 10)
        self.assertEqual(target.query("tank", 30), ["p1", "p2"])

    def test_repeated_runs_give_same_result(self):
        def run():
            target = world()
            target.post("p2", ("tank",), 20)
            target.post("p1", ("tank",), 10)
            target.post("p3", ("tank",), 10)
            target.cancel("p3", "req-1", 25)
            return target.query("tank", 30)

        self.assertEqual(run(), run())


class CancelTest(unittest.TestCase):
    def test_canceled_post_hidden(self):
        target = world()
        target.post("p1", ("tank",), 0)
        target.cancel("p1", "req-1", 1)
        self.assertEqual(target.query("tank", 2), [])

    def test_cancel_is_idempotent(self):
        target = world()
        target.post("p1", ("tank",), 0)
        self.assertTrue(target.cancel("p1", "same", 1))
        self.assertFalse(target.cancel("p1", "same", 2))

    def test_cancel_only_affects_own_posts(self):
        target = world()
        target.post("p1", ("tank",), 0)
        target.post("p2", ("tank",), 1)
        target.cancel("p1", "req-1", 2)
        self.assertEqual(target.query("tank", 3), ["p2"])

    def test_cancel_frees_player_cap(self):
        target = Board(per_player_max=1, ttl_ms=100000)
        target.post("p1", ("tank",), 0)
        target.cancel("p1", "req-1", 1)
        self.assertTrue(target.post("p1", ("tank",), 2))


class ScanTest(unittest.TestCase):
    def test_query_does_not_scan_all_posts(self):
        target = Board(per_player_max=5, ttl_ms=100000)
        for index in range(3000):
            target.post("p-%d" % index, ("tank",), index)
        for index in range(3000):
            target.query("tank", index)
        self.assertLessEqual(target.scanned_count(), 6000)

    def test_scanned_does_not_grow_with_total_posts(self):
        small = Board(per_player_max=5, ttl_ms=100000)
        for index in range(100):
            small.post("p-%d" % index, ("tank",), index)
        small.query("tank", 100)
        big = Board(per_player_max=5, ttl_ms=100000)
        for index in range(10000):
            big.post("p-%d" % index, ("tank",), index)
        big.query("tank", 10000)
        self.assertEqual(small.scanned_count(), big.scanned_count())


if __name__ == "__main__":
    unittest.main()
