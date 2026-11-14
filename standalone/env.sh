#!/bin/bash
# Common setup for the ALICE O2 simulation hands-on outside SWAN (lxplus or local build).
#
# Load the O2 environment FIRST, then source this file:
#     source standalone/env.sh
#
# It sets (override any of them before sourcing):
#   SIMTUT_DIR      work directory (default /tmp/$USER/simtutorial: local disk, not AFS/EOS)
#   SIMTUT_PROJECT  the tutorial folder (macros/, config/)
#   EX1 EX2 EX3     work directory of each exercise
#   SHMSIZE         shared memory asked by the O2DPG workflows (default 50 GB; reduced if /dev/shm is smaller)

if [ -z "${BASH_VERSION:-}" ]; then echo "env.sh: please use bash" >&2; return 1 2>/dev/null || exit 1; fi

_here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export SIMTUT_PROJECT=${SIMTUT_PROJECT:-$(dirname "$_here")}
export SIMTUT_DIR=${SIMTUT_DIR:-/tmp/${USER:-$(id -un)}/simtutorial}
export EX1=$SIMTUT_DIR/ex1 EX2=$SIMTUT_DIR/ex2 EX3=$SIMTUT_DIR/ex3
mkdir -p "$EX1" "$EX2" "$EX3"

# O2DPG asks DPL for a 50 GB shared-memory segment: use 3/4 of /dev/shm if it is smaller
if [ -z "$SHMSIZE" ]; then
  _avail=$(df -B1 --output=size /dev/shm 2>/dev/null | tail -1 | tr -d ' ')
  if [ -n "$_avail" ] && [ "$_avail" -lt 50000000000 ]; then export SHMSIZE=$((_avail * 3 / 4)); fi
  unset _avail
fi

# --- sanity checks ---
_ok=1
for _c in o2-sim root; do
  command -v "$_c" > /dev/null || { echo "env.sh: '$_c' not found - load the O2 environment first (see standalone/README.md)" >&2; _ok=0; }
done
[ -n "$O2DPG_ROOT" ] || { echo "env.sh: O2DPG_ROOT is not set - load the O2 environment first" >&2; _ok=0; }
[ -x /usr/bin/time ] || echo "env.sh: WARNING /usr/bin/time (GNU time) is missing: O2DPG workflow tasks will fail. Install the 'time' package." >&2
if ! alien-token-info > /dev/null 2>&1; then
  echo "env.sh: WARNING no valid AliEn token - run 'alien-token-init' (needed for the CCDB access in all exercises)" >&2
fi
_shm=$(df -B1 --output=size /dev/shm 2>/dev/null | tail -1 | tr -d ' ')
[ -n "$_shm" ] && [ "$_shm" -lt 2500000000 ] && echo "env.sh: WARNING /dev/shm is below 2.5 GB: exercises 2 and 3 may fail" >&2

if [ $_ok = 1 ]; then
  echo "O2_ROOT    : ${O2_ROOT}"
  echo "O2DPG_ROOT : ${O2DPG_ROOT}"
  echo "workdir    : $SIMTUT_DIR   (EX1/EX2/EX3)"
  echo "project    : $SIMTUT_PROJECT"
  [ -n "$SHMSIZE" ] && echo "SHMSIZE    : $SHMSIZE"
fi
unset _here _c _shm
_rc=$((1 - _ok)); unset _ok
return $_rc 2>/dev/null || exit $_rc
