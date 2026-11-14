#!/bin/bash
# Exercise 1 - simplest o2-sim runs. Usage (after loading O2): bash standalone/run_ex1.sh
set -e
source "$(dirname "$0")/env.sh"
NJ=${NJ:-4}          # transport workers
cd "$EX1"
echo "### 1a Pythia8 pp, full detector"
time o2-sim -n 4 -g pythia8pp -j $NJ --seed 42 > sim_pythia.log 2>&1
tail -3 sim_pythia.log
grep -m1 'We collide' o2sim_serverlog
echo "### 1b kinematics"
root -l -b -q "$SIMTUT_PROJECT/macros/kineOverview.C(\"o2sim_Kine.root\",\"kine_pythia.svg\")"
echo "### 1c generator only / fewer modules"
time o2-sim -n 100 -g pythia8pp --noGeant -o gen_only > gen_only.log 2>&1
time o2-sim -n 4 -g pythia8pp -j $NJ -m PIPE ITS TPC -o itstpc > itstpc.log 2>&1
ls -lh ./*_Kine.root
echo "### 1d Lc box gun"
time o2-sim -n 10 -g boxgen -j $NJ -m PIPE ITS TPC -o lambdac \
  --configKeyValues "BoxGun.pdg=4122;BoxGun.number=5;BoxGun.eta[0]=-0.8;BoxGun.eta[1]=0.8;BoxGun.prange[0]=1.;BoxGun.prange[1]=10.;BoxGun.phirange[0]=0.;BoxGun.phirange[1]=360." \
  > lambdac.log 2>&1
root -l -b -q "$SIMTUT_PROJECT/macros/kineDaughters.C(\"lambdac_Kine.root\",4122)"
echo "Exercise 1 done: results in $EX1"
