#!/bin/bash
# Exercise 2 - O2DPG workflow with the hybrid generator, up to the AOD.
# Usage (after loading O2): bash standalone/run_ex2.sh      (NS=signal events, NJ=workers, CPU/MEM limits)
set -e
source "$(dirname "$0")/env.sh"
NS=${NS:-4}; NJ=${NJ:-4}; CPU=${CPU:-4}; MEM=${MEM:-14000}
cd "$EX2"
cp "$SIMTUT_PROJECT/config/hybrid_pp_cocktail.json" .
echo "### 2a quick check"
o2-sim -n 2 -g hybrid --noGeant -o hybtest \
  --configKeyValues "GeneratorHybrid.configFile=$EX2/hybrid_pp_cocktail.json" > hybtest.log 2>&1
root -l -b -q "$SIMTUT_PROJECT/macros/kineDaughters.C(\"hybtest_Kine.root\",4122)" | grep '^event'
echo "### 2b workflow"
${O2DPG_ROOT}/MC/bin/o2dpg_sim_workflow.py -eCM 14000 -col pp -gen hybrid \
  -confKey "GeneratorHybrid.configFile=$EX2/hybrid_pp_cocktail.json" \
  -tf 1 -ns $NS -j $NJ -interactionRate 500000 -run 302000 -seed 42 2>&1 | tail -5
echo "### 2c run up to the AOD"
time ${O2DPG_ROOT}/MC/bin/o2_dpg_workflow_runner.py -f workflow.json -tt aod \
  --cpu-limit $CPU --mem-limit $MEM --stdout-on-failure > runner_aod.log 2>&1
tail -3 runner_aod.log
echo "### 2d AOD"
root -l -b -q "$SIMTUT_PROJECT/macros/aodMcSummary.C(\"AO2D.root\",4122)"
