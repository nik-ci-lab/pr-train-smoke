"""Synthetic test suite. Each package check costs PKG_SECONDS; integration costs INT_SECONDS.

Change files (pkgs/<pkg>/changes/*.py) are what agent PRs add. Their flags drive failures:
  VALID = False              -> the package's own check fails (Gate 1 catches it)
  BREAKS_INTEGRATION = True  -> only the integration check fails (Gate 1 misses it: a "graph miss")
  EXCLUSIVE = "<token>"      -> fails only when two change files claim the same token (interaction)
"""
import glob
import importlib.util
import os
import random
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKGS = [f"p{i}" for i in range(10)]
PKG_SECONDS = 15
INT_SECONDS = 30
FLAKE_RATE = 0.03


def _load(path):
    spec = importlib.util.spec_from_file_location("chg_" + os.path.basename(path)[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _changes(pkgs):
    out = []
    for p in pkgs:
        for f in sorted(glob.glob(os.path.join(ROOT, "pkgs", p, "changes", "*.py"))):
            out.append((os.path.relpath(f, ROOT).replace("\\", "/"), _load(f)))
    return out


def check_pkg(pkg):
    time.sleep(PKG_SECONDS)
    bad = [f for f, m in _changes([pkg]) if not getattr(m, "VALID", True)]
    if bad:
        raise AssertionError(f"{pkg}: invalid change files {bad}")


def check_integration():
    time.sleep(INT_SECONDS)
    allc = _changes(PKGS)
    breaks = [f for f, m in allc if getattr(m, "BREAKS_INTEGRATION", False)]
    if breaks:
        raise AssertionError(f"integration broken by {breaks}")
    seen = {}
    for f, m in allc:
        tok = getattr(m, "EXCLUSIVE", None)
        if tok:
            if tok in seen:
                raise AssertionError(f"exclusive resource {tok!r} claimed by {seen[tok]} and {f}")
            seen[tok] = f


def check_flaky():
    time.sleep(2)
    if random.random() < FLAKE_RATE:
        raise AssertionError("flaky: transient failure")
