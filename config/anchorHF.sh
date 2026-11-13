#!/bin/bash
# Anchored MC example with an external generator (PWGHF gap-triggered charm+beauty)
# Anchoring: pp 13.6 TeV, LHC23f, run 535069, apass2

# --- anchoring ---
export ALIEN_JDL_LPMANCHORPASSNAME=apass2
export ALIEN_JDL_MCANCHOR=apass2
export ALIEN_JDL_CPULIMIT=${ALIEN_JDL_CPULIMIT:-4}     # cores available (SWAN: 4)
export ALIEN_JDL_LPMRUNNUMBER=535069
export ALIEN_JDL_LPMPRODUCTIONTYPE=MC
export ALIEN_JDL_LPMINTERACTIONTYPE=pp
export ALIEN_JDL_LPMPRODUCTIONTAG=LHC26tutorial
export ALIEN_JDL_LPMANCHORRUN=535069
export ALIEN_JDL_LPMANCHORPRODUCTION=LHC23f
export ALIEN_JDL_LPMANCHORYEAR=2023

# --- slice of the run (on the GRID these come from grid_submit.sh) ---
export NTIMEFRAMES=1
export NSIGEVENTS=${NSIGEVENTS:-6}
export PRODSPLIT=${ALIEN_O2DPG_GRIDSUBMIT_PRODSPLIT:-100}
export SPLITID=${ALIEN_O2DPG_GRIDSUBMIT_SUBJOBID:-50}
export CYCLE=0
export SEED=${SEED:-5}
export NWORKERS=${NWORKERS:-2}

# --- the external generator ---
export ALIEN_JDL_ANCHOR_SIM_OPTIONS="-gen external -ini ${O2DPG_MC_CONFIG_ROOT}/MC/config/PWGHF/ini/GeneratorHF_D2H_ccbar_and_bbbar_gap3.ini"

# --- no QC for the tutorial ---
export DISABLE_QC=1

${O2DPG_ROOT}/MC/run/ANCHOR/anchorMC.sh
