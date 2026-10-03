"""命令行入口：跑组队板样例。"""

import argparse

from .core import Board


def build_parser():
    parser = argparse.ArgumentParser(prog="party-board", description="组队板")
    parser.add_argument("--sample", default="cap",
                        help="cap / ttl / filter / order / cancel / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "cap":
        world = Board(per_player_max=2, ttl_ms=100000)
        ok = True
        for index in range(3):
            ok = world.post("p1", ("tank",), index)
        print("third=%s" % str(ok).lower())
    elif args.sample == "ttl":
        world = Board(per_player_max=5, ttl_ms=1000)
        world.post("p1", ("tank",), 0)
        print("pending=%d" % len(world.query("tank", 1001)))
    elif args.sample == "filter":
        world = Board(per_player_max=5, ttl_ms=100000)
        world.post("p1", ("tank",), 0)
        world.post("p2", ("healer",), 1)
        print("found=%s" % ",".join(world.query("tank", 10)))
    elif args.sample == "order":
        world = Board(per_player_max=5, ttl_ms=100000)
        world.post("p2", ("tank",), 20)
        world.post("p1", ("tank",), 10)
        print("order=%s" % ",".join(world.query("tank", 30)))
    elif args.sample == "cancel":
        world = Board(per_player_max=5, ttl_ms=100000)
        world.post("p1", ("tank",), 0)
        world.cancel("p1", "same", 1)
        second = world.cancel("p1", "same", 2)
        print("second=%s" % str(second).lower())
    elif args.sample == "scan":
        world = Board(per_player_max=5, ttl_ms=100000)
        for index in range(3000):
            world.post("p-%d" % index, ("tank",), index)
        for index in range(3000):
            world.query("tank", index)
        print("scanned=%d" % world.scanned_count())
    else:
        raise SystemExit("需要 --sample cap|ttl|filter|order|cancel|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
