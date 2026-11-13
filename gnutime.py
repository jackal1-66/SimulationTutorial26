"""Minimal stand-in for GNU time, used by o2exec when /usr/bin/time is missing (e.g. on SWAN).

O2's jobutils2.sh runs every O2DPG workflow task as
    TIME="..." /usr/bin/time --output=<task>.log_time ./<task>.log_tmp.sh
o2exec gives the workflows a copy of jobutils2.sh that calls this script instead.

usage: python3 gnutime.py [--output=FILE | -o FILE] command [args...]
Runs the command, forwards SIGINT/SIGTERM to it, writes the timing summary in the
format used by jobutils2.sh and exits with the exit code of the command.
"""
import os
import resource
import signal
import subprocess
import sys
import time


def main():
    args = sys.argv[1:]
    output = None
    while args and args[0].startswith("-"):
        opt = args.pop(0)
        if opt.startswith("--output="):
            output = opt.split("=", 1)[1]
        elif opt in ("-o", "--output") and args:
            output = args.pop(0)
        elif opt == "--":
            break
    if not args:
        print("gnutime.py: no command given", file=sys.stderr)
        return 2

    start = time.time()
    try:
        child = subprocess.Popen(args)
    except OSError as e:
        print(f"gnutime.py: cannot run {args[0]}: {e}", file=sys.stderr)
        return 127

    def forward(signum, _frame):
        try:
            child.send_signal(signum)
        except ProcessLookupError:
            pass

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, forward)

    rc = child.wait()
    wall = time.time() - start
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = 100.0 * (usage.ru_utime + usage.ru_stime) / wall if wall > 0 else 0.0

    lines = []
    if rc != 0:
        lines.append(f"Command exited with non-zero status {rc if rc > 0 else 128 - rc}")
    lines += [f"#walltime {wall:.2f}", f"#systime {usage.ru_stime:.2f}", f"#usertime {usage.ru_utime:.2f}",
              f"#maxmem {usage.ru_maxrss}", f"#CPU {cpu:.0f}%"]
    text = "\n".join(lines) + "\n"
    if output:
        with open(output, "w") as f:
            f.write(text)
    else:
        sys.stderr.write(text)
    return rc if rc >= 0 else 128 - rc


if __name__ == "__main__":
    sys.exit(main())
