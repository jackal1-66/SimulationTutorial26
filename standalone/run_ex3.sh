#!/bin/bash
# Exercise 3 - anchored MC with the PWGHF external generator (30-45 min on 4 cores).
# Usage (after loading O2): bash standalone/run_ex3.sh     (NSIGEVENTS, NWORKERS, ALIEN_JDL_CPULIMIT can be overridden)
set -e
source "$(dirname "$0")/env.sh"
cd "$EX3"
bash "$SIMTUT_PROJECT/config/anchorHF.sh" > anchor.log 2>&1
grep -m20 -iE "timestamp|interaction ?rate|detectors|colliding|SOR|EOR" anchor.log | cut -c1-200
root -l -b -q "$SIMTUT_PROJECT/macros/aodMcSummary.C(\"AO2D.root\",421)"
