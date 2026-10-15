"""Pick the gate mode and test shards for this run. Writes mode= and shards= to $GITHUB_OUTPUT.

Modes (LAB_MODE=trains):
  G1   pull_request into qa-intake           -> changed packages only (no integration: deliberate graph miss)
  G2a  pull_request train/* into qa          -> full suite, 4 shards
  G2b  merge_group                           -> this entry's changed packages + integration (HEAD^1..HEAD)
  REJECT any other PR into qa               -> fail
Baseline (LAB_MODE=baseline): pull_request into qa -> G1; merge_group -> full suite per queued PR.
workflow_dispatch -> full suite (canary).
"""
import json
import os
import subprocess

FULL = ["p0 p1 p2", "p3 p4 p5", "p6 p7 p8", "p9 integration flaky"]


def changed():
    out = subprocess.run(["git", "diff", "--name-only", "HEAD^1", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.split()
    pkgs, barrier = set(), False
    for f in out:
        parts = f.split("/")
        if parts[0] == "pkgs" and len(parts) > 1 and parts[1].startswith("p"):
            pkgs.add(parts[1])
        elif parts[0] in ("ci", ".github"):
            barrier = True
    return sorted(pkgs), barrier, out


def main():
    ev = os.environ["EVENT"]
    lab = os.environ.get("LAB_MODE") or "trains"
    base = os.environ.get("BASE_REF", "")
    head = os.environ.get("HEAD_REF", "")
    pkgs, barrier, files = changed()
    print(f"event={ev} lab={lab} base={base} head={head} files={files}")

    if ev == "workflow_dispatch" or barrier:
        mode, shards = "FULL", FULL
    elif ev == "merge_group":
        if lab == "baseline":
            mode, shards = "G2b-full", FULL
        else:
            mode = "G2b"
            shards = ([" ".join(pkgs)] if pkgs else []) + ["integration flaky"]
    elif lab == "trains" and base == "qa":
        if head.startswith("train/"):
            mode, shards = "G2a", FULL
        else:
            mode, shards = "REJECT", []
    else:
        mode, shards = "G1", ([" ".join(pkgs)] if pkgs else [])

    print(f"mode={mode} shards={shards}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        fh.write(f"mode={mode}\n")
        fh.write(f"shards={json.dumps(shards)}\n")


if __name__ == "__main__":
    main()
