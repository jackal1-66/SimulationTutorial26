"""Common setup for the ALICE O2 simulation hands-on on SWAN.

Import it at the top of every notebook:   from swan_env import *

- puts the project folder (with the `o2exec` wrapper) in PATH
- defines the scratch working directory SIMTUT_DIR (local disk, not CERNBox)
- provides small helpers to run long jobs in the background and to show plots
"""
import getpass
import os
import pathlib
import shutil
import subprocess

PROJECT = pathlib.Path(__file__).resolve().parent
USER = getpass.getuser()

# O2PDPSuite release from CVMFS (change here for the whole tutorial)
O2SIM_TAG = os.environ.setdefault("O2SIM_TAG", "VO_ALICE@O2PDPSuite::MC-prod-2026-v14-1")

# Simulations run on the local disk of the SWAN session: CERNBox (EOS) is slow
# for the many small files written by the workflows.
# The O2DPG workflow runner EXECUTES small scripts in the work directory, so the
# directory must be on a filesystem that allows it (/tmp may be mounted "noexec").


def _can_execute_in(d):
    """True if directory d can be created and a script in it can be executed."""
    try:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / ".exec_probe.sh"
        probe.write_text("#!/bin/sh\nexit 0\n")
        probe.chmod(0o755)
        ok = subprocess.run([str(probe)], capture_output=True).returncode == 0
        probe.unlink()
        return ok
    except Exception:
        return False


def _choose_workdir():
    if os.environ.get("SIMTUT_DIR"):  # set by the user: take it as it is
        return pathlib.Path(os.environ["SIMTUT_DIR"]), []
    candidates = [pathlib.Path(f"/tmp/{USER}/simtutorial"),
                  pathlib.Path(f"/var/tmp/{USER}/simtutorial"),
                  pathlib.Path.home() / "simtutorial_work"]  # CERNBox: works, but slower
    rejected = []
    for d in candidates:
        if _can_execute_in(d):
            return d, rejected
        rejected.append(d)
    return candidates[-1], rejected


WORKDIR, _rejected = _choose_workdir()
WORKDIR.mkdir(parents=True, exist_ok=True)
os.environ["SIMTUT_DIR"] = str(WORKDIR)
for _d in _rejected:
    print(f"note: cannot execute programs in {_d} (mounted noexec?) - not used as work directory")

# Final results are copied here (CERNBox, survives the session)
RESULTS = pathlib.Path.home() / "simtutorial_results"

# Local copy of the project files used by the O2 programs (macros, configs, o2exec).
# The project itself is on CERNBox (EOS): programs started through o2exec run in a
# clean environment and cannot always read EOS, and SWAN uploads drop the
# executable bit. The copy is refreshed every time a notebook imports this module.
LOCAL = WORKDIR / "project"
LOCAL.mkdir(parents=True, exist_ok=True)
for sub in ("macros", "config"):
    shutil.copytree(PROJECT / sub, LOCAL / sub, dirs_exist_ok=True)
shutil.copy(PROJECT / "o2exec", LOCAL / "o2exec")
shutil.copy(PROJECT / "gnutime.py", LOCAL / "gnutime.py")
for f in [LOCAL / "o2exec", *(LOCAL / "config").glob("*.sh")]:
    f.chmod(0o755)

os.environ["SIMTUT_PROJECT"] = str(LOCAL)
if str(LOCAL) not in os.environ["PATH"].split(":"):
    os.environ["PATH"] = f"{LOCAL}:{os.environ['PATH']}"


def workdir(name):
    """Create and return the working directory of one exercise."""
    d = WORKDIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def show(img):
    """Display a plot produced by a ROOT macro (SVG or PNG)."""
    from IPython.display import SVG, Image, display
    img = str(img)
    display(SVG(filename=img) if img.endswith(".svg") else Image(filename=img))


def start(command, cwd, log):
    """Start `command` (a bash string) in the O2 environment, in the background.

    The job keeps running if the cell is interrupted; follow it with status().
    """
    cwd = pathlib.Path(cwd)
    logfile = cwd / log
    with open(logfile, "w") as out:
        p = subprocess.Popen(["bash", str(LOCAL / "o2exec"), "bash", "-c", command], cwd=cwd,
                             stdout=out, stderr=subprocess.STDOUT,
                             start_new_session=True)
    (cwd / (log + ".pid")).write_text(str(p.pid))
    print(f"started PID {p.pid} in {cwd}\nlog: {logfile}")
    return p


def status(cwd, log, n=15):
    """Print whether the background job is still running and the end of its log."""
    cwd = pathlib.Path(cwd)
    pidfile = cwd / (log + ".pid")
    running = False
    if pidfile.exists():
        pid = int(pidfile.read_text())
        running = subprocess.run(["ps", "-p", str(pid)], capture_output=True).returncode == 0
        print(f"PID {pid}: {'RUNNING' if running else 'FINISHED'}")
    print("-" * 80)
    print(subprocess.run(["tail", "-n", str(n), str(cwd / log)], capture_output=True, text=True).stdout)
    return running


def stop(cwd, log):
    """Kill a background job started with start()."""
    pidfile = pathlib.Path(cwd) / (log + ".pid")
    pid = int(pidfile.read_text())
    subprocess.run(["kill", "--", f"-{pid}"])  # whole process group
    print(f"sent SIGTERM to process group {pid}")


# ---------------------------------------------------------------------------
# %%bash cells run inside the O2 environment
# ---------------------------------------------------------------------------
class BashCellError(Exception):
    """A %%bash cell finished with a non-zero exit code."""

    def _render_traceback_(self):  # IPython: show one clear line instead of a traceback
        return [f"\x1b[31mERROR: {self} - check the output above\x1b[0m"]


def run_in_o2(script):
    """Run a bash script in the O2 environment, streaming its output. Returns the exit code."""
    import signal
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".sh", prefix="cell_", dir=WORKDIR, delete=False) as f:
        f.write(script)
    try:
        p = subprocess.Popen(["bash", str(LOCAL / "o2exec"), "bash", f.name], stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, errors="replace", bufsize=1, start_new_session=True)
        try:
            for line in p.stdout:
                print(line, end="", flush=True)
            return p.wait()
        except KeyboardInterrupt:  # stop button: terminate the whole job
            os.killpg(p.pid, signal.SIGTERM)
            p.wait()
            print("\n[stopped]")
            raise
    finally:
        os.unlink(f.name)


def _bash_cell(line, cell):
    rc = run_in_o2(cell)
    if rc != 0:
        raise BashCellError(f"the cell finished with exit code {rc}") from None


try:
    from IPython import get_ipython
    _ip = get_ipython()
except ImportError:
    _ip = None
if _ip is not None:
    # replaces the standard %%bash magic in this notebook
    _ip.register_magic_function(_bash_cell, magic_kind="cell", magic_name="bash")


# Shared memory: DPL reconstruction steps of the workflows allocate segments in /dev/shm.
# With a very small /dev/shm (e.g. 64 MB) some workflow tasks fail.
try:
    _shm = os.statvfs("/dev/shm")
    _shm_gb = _shm.f_frsize * _shm.f_blocks / 1e9
    if _shm_gb < 2.5:
        print(f"WARNING: /dev/shm is only {_shm_gb:.2f} GB in this session: the O2DPG workflows "
              "(exercises 2 and 3) need a few GB and may fail. Exercise 1 is not affected.")
except OSError:
    pass


print(f"project : {PROJECT}\nlocal   : {LOCAL}\nO2 tag  : {O2SIM_TAG}\nworkdir : {WORKDIR}\nresults : {RESULTS}")
