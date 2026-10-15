"""Run a shard: argv[1] is a space-separated list of targets (p0..p9, integration, flaky).

Only the known-flaky target is retried (once); real checks are never retried.
"""
import sys
import traceback

import checks

RETRY = {"flaky"}


def run(target):
    if target == "integration":
        checks.check_integration()
    elif target == "flaky":
        checks.check_flaky()
    else:
        checks.check_pkg(target)


def main():
    targets = sys.argv[1].split()
    if not targets:
        print("no targets: nothing executed")
        return 1
    failed = []
    for t in targets:
        for attempt in (1, 2):
            try:
                run(t)
                print(f"PASS {t}" + (" (after retry)" if attempt == 2 else ""))
                break
            except AssertionError as e:
                print(f"FAIL {t} attempt {attempt}: {e}")
                if t not in RETRY or attempt == 2:
                    failed.append(t)
                    break
            except Exception:
                traceback.print_exc()
                failed.append(t)
                break
    print(f"executed={len(targets)} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
