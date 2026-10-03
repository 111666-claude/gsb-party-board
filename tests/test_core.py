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


class CapTest(unittest.TestCase):
    def test_post_beyond_cap_returns_false(self):
        target = Board(per_player_max=2, ttl_ms=100000)
        self.assertTrue(target.post("p1", ("tank",), 0))
        self.assertTrue(target.post("p1", ("tank",), 1))
        self.assertFalse(target.post("p1", ("tank",), 2))

    def test_cap_counts_each_player_separately(self):
        target = Board(per_player_max=1, ttl_ms=100000)
        self.assertTrue(target.post("p1", ("tank",), 0))
        self.assertTrue(target.post("p2", ("tank",), 0))
        self.assertFalse(target.post("p1", ("tank",), 1))

    def test_expired_post_frees_cap_slot(self):
        target = Board(per_player_max=1, ttl_ms=100)
        self.assertTrue(target.post("p1", ("tank",), 0))
        self.assertTrue(target.post("p1", ("tank",), 101))

    def test_cancel_frees_cap_slot(self):
        target = Board(per_player_max=1, ttl_ms=100000)
        self.assertTrue(target.post("p1", ("tank",), 0))
        target.cancel("p1", "r1", 1)
        self.assertTrue(target.post("p1", ("tank",), 2))


class TtlTest(unittest.TestCase):
    def test_expired_post_not_returned(self):
        target = Board(per_player_max=5, ttl_ms=1000)
        target.post("p1", ("tank",), 0)
        self.assertEqual(target.query("tank", 1001), [])

    def test_post_at_exact_ttl_still_visible(self):
        target = Board(per_player_max=5, ttl_ms=1000)
        target.post("p1", ("tank",), 0)
        self.assertEqual(target.query("tank", 1000), ["p1"])

    def test_fresh_post_survives_purge(self):
        target = Board(per_player_max=5, ttl_ms=1000)
        target.post("p1", ("tank",), 0)
        target.post("p2", ("tank",), 900)
        self.assertEqual(target.query("tank", 1001), ["p2"])


class FilterTest(unittest.TestCase):
    def test_query_returns_only_matching_role(self):
        target = world()
        target.post("p1", ("tank",), 0)
        target.post("p2", ("healer",), 1)
        self.assertEqual(target.query("tank", 10), ["p1"])
        self.assertEqual(target.query("healer", 10), ["p2"])

    def test_multi_role_post_matches_each_role(self):
        target = world()
        target.post("p1", ("tank", "healer"), 0)
        self.assertEqual(target.query("tank", 0), ["p1"])
        self.assertEqual(target.query("healer", 0), ["p1"])


class OrderTest(unittest.TestCase):
    def test_results_sorted_by_time_then_player(self):
        target = world()
        target.post("p2", ("tank",), 20)
        target.post("p1", ("tank",), 10)
        target.post("p0", ("tank",), 20)
        self.assertEqual(target.query("tank", 30), ["p1", "p0", "p2"])

    def test_same_time_sorted_by_player_id(self):
        target = world()
        target.post("p9", ("tank",), 5)
        target.post("p1", ("tank",), 5)
        self.assertEqual(target.query("tank", 5), ["p1", "p9"])

    def test_repeated_sequence_gives_same_results(self):
        def run():
            target = world()
            target.post("p2", ("tank",), 20)
            target.post("p1", ("tank",), 10)
            target.cancel("p2", "r1", 25)
            return target.query("tank", 30)
        self.assertEqual(run(), run())


class CancelTest(unittest.TestCase):
    def test_cancel_hides_post(self):
        target = world()
        target.post("p1", ("tank",), 0)
        target.cancel("p1", "r1", 1)
        self.assertEqual(target.query("tank", 2), [])

    def test_cancel_is_idempotent_per_req_id(self):
        target = world()
        target.post("p1", ("tank",), 0)
        self.assertTrue(target.cancel("p1", "same", 1))
        self.assertFalse(target.cancel("p1", "same", 2))

    def test_cancel_only_removes_own_posts(self):
        target = world()
        target.post("p1", ("tank",), 0)
        target.post("p2", ("tank",), 1)
        target.cancel("p1", "r1", 2)
        self.assertEqual(target.query("tank", 3), ["p2"])


class ScanTest(unittest.TestCase):
    def test_scanned_does_not_grow_with_total_posts(self):
        target = Board(per_player_max=5, ttl_ms=10 ** 12)
        for index in range(3000):
            target.post("p-%d" % index, ("tank",), index)
        before = target.scanned_count()
        for index in range(3000):
            target.query("healer", index)
        self.assertEqual(target.scanned_count(), before)

    def test_scan_sample_budget(self):
        target = Board(per_player_max=5, ttl_ms=100000)
        for index in range(3000):
            target.post("p-%d" % index, ("tank",), index)
        for index in range(3000):
            target.query("tank", index)
        self.assertLessEqual(target.scanned_count(), 6000)
