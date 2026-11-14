# ALICE Run 3 simulation hands-on on lxplus or on your own machine

Same hands-on as the SWAN notebooks (`00_setup` … `03_anchored_external`), run from a normal terminal.
You load the O2 environment **once**, source `standalone/env.sh`, and then type the commands as they are.

| | lxplus | Local machine |
|---|---|---|
| Software | O2 from CVMFS | O2sim built with `aliBuild` |
| Setup time | a few minutes | **hours** (build) |
| Needs | an lxplus account (AlmaLinux 9) | AlmaLinux 9 or similar, ≥ 16 GB RAM, ~100 GB free disk for the build |
| Both | ALICE grid certificate (you must be in the ALICE VO), 4 cores, 16 GB RAM, ~10 GB of scratch space for the exercises | |

> **Do not run the exercises in AFS or EOS.** Workflows write many small files and execute scripts in the work directory.
> `env.sh` uses `/tmp/$USER/simtutorial` by default (set `SIMTUT_DIR` before sourcing to change it). On lxplus `/tmp` is local to the node and is cleaned: copy the results you want to keep.

---

## 1. Get the project

```bash
git clone https://github.com/jackal1-66/SimulationTutorial26
cd SimulationTutorial26
```

## 2. Load the O2 environment

### A. lxplus (CVMFS)

```bash
ssh <user>@lxplus9.cern.ch
/cvmfs/alice.cern.ch/bin/alienv enter VO_ALICE@O2PDPSuite::MC-prod-2026-v14-1
```

This opens a new shell with `o2-sim`, `root` and `$O2DPG_ROOT`. The first call downloads software into the CVMFS cache and can take a few minutes. Type `exit` to leave it.
The tag is the one the SWAN version uses. To see the available tags: `/cvmfs/alice.cern.ch/bin/alienv q | grep MC-prod`.

> lxplus nodes are shared. Use `-j 2` instead of `-j 4`, and a smaller number of events, if the exercises are slow.

### B. Local machine: build with aliBuild

This takes hours and a lot of disk space; do it **before** the event. Full documentation: <https://alisw.github.io/alibuild/user.html> and <https://aliceo2group.github.io/>.

```bash
python3 -m pip install --user alibuild          # needs Python 3 and git
export PATH=$HOME/.local/bin:$PATH
mkdir -p ~/alice && cd ~/alice
aliBuild init O2sim@dev --defaults o2           # clones alidist
cd alidist && git checkout <tag>  ; cd ..       # optional: a tagged alidist, e.g. the one of the release you want
aliDoctor O2sim --defaults o2                   # checks and lists the system packages you are missing
aliBuild build O2sim --defaults o2 -j <ncores>  # hours
```

`aliDoctor` tells you which system packages to install. The `O2sim` package contains O2, O2DPG and the event generators; `O2PDPSuite` is the same plus more packages and works too.

Load it:

```bash
cd ~/alice
alienv -w ~/alice/sw enter O2sim/latest         # "latest" or a specific version, see: alienv -w ~/alice/sw q | grep O2sim
```

> If your shell defines an `alienv` function (from `alienv shell-helper`) and `alienv enter` does not behave, call the script directly: `~/.local/bin/alienv -w ~/alice/sw enter O2sim/latest`.

## 3. Grid token

When `o2-sim` transports particles it reads the detector alignment from CCDB, and the O2DPG workflows read many calibration objects. Part of them needs an **AliEn token**. Your certificate must be in `~/.globus/usercert.pem` and `~/.globus/userkey.pem` (permissions `644` and `400`). Then, inside the O2 environment:

```bash
alien-token-init       # asks your grid-certificate password (not your CERN password)
alien-token-info       # shows the token validity
```

On lxplus, if your certificate is on AFS, `~/.globus` already works. The token is written to `/tmp/tokencert_<uid>.pem`.

## 4. Check the setup

Inside the O2 environment, from the project folder:

```bash
source standalone/env.sh
```

It prints `O2_ROOT`, `O2DPG_ROOT` and the work directory, and warns about a missing token, a missing `/usr/bin/time` or a too small `/dev/shm`.
It defines `$EX1`, `$EX2`, `$EX3` (work directories of the exercises) and `$SIMTUT_PROJECT` (the project folder, with `macros/` and `config/`).
Do this in **every new shell**, after loading O2.

```bash
o2-sim --help | head -40
```

> Each exercise below also has a one-shot script (`standalone/run_ex1.sh`, `run_ex2.sh`, `run_ex3.sh`) that runs all its steps. Use them to check your setup quickly; do the exercises step by step to learn.

---

## Exercise 1: the simplest simulation with `o2-sim`

`o2-sim` creates the ALICE geometry, generates primary particles, transports them with Geant4 and writes hits and the MC kinematics.

### 1a. Pythia8 pp events, full detector

4 minimum-bias pp events (`pythia8pp`, √s = 14 TeV), Geant4, 4 workers. Most of the time is initialisation.

```bash
cd $EX1
time o2-sim -n 4 -g pythia8pp -j 4 --seed 42 > sim_pythia.log 2>&1
tail -5 sim_pythia.log
ls -lh
```

> Without a valid token the worker stops with `TGrid::Connect returned nullptr`. As a workaround add `--configKeyValues "align-geom.mDetectors=none"` (ideal geometry).

| File | Content |
|---|---|
| `o2sim_Kine.root` | MC kinematics: primary and secondary particles (`o2::MCTrack`) |
| `o2sim_MCHeader.root` | event-level information (impact parameter, generator info, …) |
| `o2sim_geometry.root`, `o2sim_grp.root` | geometry and run parameters used |
| `o2sim_<DET>.root` | hits of each detector |
| `o2sim_serverlog`, `o2sim_workerlog0`, `o2sim_mergerlog` | logs of the event server, transport workers and hit merger |

**Questions**
1. How many hit files were produced? Which detectors are simulated by default?
2. Find the Pythia8 initialisation in `o2sim_serverlog`. Which beams and energy were used?

```bash
grep -m1 'We collide' o2sim_serverlog
cfg=$(grep -m1 -oE 'Reading configuration from file: [^ ]+' o2sim_serverlog | awk '{print $NF}')
echo "Pythia8 config: $cfg"
grep -E '^ *Beams:' "$cfg"
```

> Pythia8 only lists the settings that differ from its defaults in its "Changed Settings" table.

### 1b. A look at the kinematics

The tree `o2sim` has one entry per event, each holding a `std::vector<o2::MCTrack>`. `root` is the one of the O2 environment, so the O2 classes are known.

```bash
cd $EX1
root -l -b -q "$SIMTUT_PROJECT/macros/kineOverview.C(\"o2sim_Kine.root\",\"kine_pythia.svg\")"
```

View `kine_pythia.svg` with a browser or `display`. On lxplus copy it to your laptop: `scp <user>@lxplus9.cern.ch:/tmp/<user>/simtutorial/ex1/kine_pythia.svg .`

### 1c. Make it faster

- `--noGeant`: generator output only, no transport (seconds).
- `-m PIPE ITS TPC`: only some modules in the geometry.

```bash
cd $EX1
echo "### generator only"; time o2-sim -n 100 -g pythia8pp --noGeant -o gen_only > gen_only.log 2>&1
echo "### PIPE+ITS+TPC";   time o2-sim -n 4 -g pythia8pp -j 4 -m PIPE ITS TPC -o itstpc > itstpc.log 2>&1
ls -lh *_Kine.root
```

**Question.** Compare the time per event and the size of the kinematics files with 1a. Why is `gen_only_Kine.root` so small even with 100 events?

> Predefined detector sets can be chosen with `--detectorList`: `ALICE2` (Run 3), `ALICE2.1` (Run 4), `ALICE3` (Run 5/6).

### 1d. A box generator: Λc⁺ gun

`boxgen` shoots `BoxGun.number` particles of type `BoxGun.pdg`, uniform in η, p and φ. Here 5 Λc⁺ (PDG 4122) per event, |η| < 0.8, 1 < p < 10 GeV/c.

```bash
cd $EX1
time o2-sim -n 10 -g boxgen -j 4 -m PIPE ITS TPC -o lambdac \
  --configKeyValues "BoxGun.pdg=4122;BoxGun.number=5;BoxGun.eta[0]=-0.8;BoxGun.eta[1]=0.8;BoxGun.prange[0]=1.;BoxGun.prange[1]=10.;BoxGun.phirange[0]=0.;BoxGun.phirange[1]=360." \
  > lambdac.log 2>&1
tail -3 lambdac.log
root -l -b -q "$SIMTUT_PROJECT/macros/kineDaughters.C(\"lambdac_Kine.root\",4122)"
```

**Questions**
1. Which decay products of the Λc⁺ do you find, and in which proportions? Is this what you expect from the PDG? Who decays the Λc⁺ here, the generator or the transport code, and with which decay table? (For physics samples, PWG configurations set the Λc⁺ decays at generator level.)
2. Change the gun to π⁺ (`BoxGun.pdg=211`) and compare the number of tracks per event, i.e. the secondaries produced in the material.

> Boxgen can also sample uniformly in pT and rapidity: add `BoxGun.sampleYAndPt=true`, and `eta`/`prange` are then read as y and pT ranges.

---

## Exercise 2: O2DPG workflow with the hybrid generator

The **hybrid generator** combines several generators configured in one JSON file. `config/hybrid_pp_cocktail.json` defines two entries used alternately:
1. plain `pythia8pp` (no cocktail);
2. a **cocktail** of `pythia8pp` + `boxgen` injecting 5 Λc⁺ into the same event.

With `"fractions": [1, 1]`: one plain event, then one cocktail event, and so on. Then you run the full MC chain up to the AOD with two O2DPG steps:
1. `o2dpg_sim_workflow.py` creates `workflow.json` (a graph of tasks);
2. `o2_dpg_workflow_runner.py` runs it.

```bash
cd $EX2
cp $SIMTUT_PROJECT/config/hybrid_pp_cocktail.json .
cat hybrid_pp_cocktail.json
```

Notes on the JSON:
- `pythia8pp` needs no `config` block. `boxgen`, `pythia8`, `external` and `hepmc` must have one.
- A `cocktail` is **one** entry in `fractions`: `[1, 0]` gives only plain events, `[0, 1]` only cocktail events.
- A template can be generated with `$O2DPG_ROOT/MC/bin/o2_hybrid_gen.py --gen pythia8pp boxgen --output template.json`.

### 2a. Quick check with `o2-sim` only

Always test a new configuration with a few events and `--noGeant`:

```bash
cd $EX2
o2-sim -n 2 -g hybrid --noGeant -o hybtest \
   --configKeyValues "GeneratorHybrid.configFile=$EX2/hybrid_pp_cocktail.json" > hybtest.log 2>&1
grep -iE 'hybrid' hybtest.log | head -20
root -l -b -q "$SIMTUT_PROJECT/macros/kineDaughters.C(\"hybtest_Kine.root\",4122)" | grep '^event'
```

### 2b. Create the workflow

- `-gen hybrid` + `-confKey "GeneratorHybrid.configFile=..."`: the generator setup.
- `-eCM 14000`: matches the energy of `pythia8pp`.
- `-tf 1 -ns 4`: 1 timeframe with 4 signal events.
- `-interactionRate 500000`: 500 kHz pp.
- `-run 302000`: a predefined pp MC run number (for CCDB conditions).
- `-j 4`: 4 transport workers (default 8 = GRID node).

```bash
cd $EX2
${O2DPG_ROOT}/MC/bin/o2dpg_sim_workflow.py \
    -eCM 14000 -col pp -gen hybrid \
    -confKey "GeneratorHybrid.configFile=$EX2/hybrid_pp_cocktail.json" \
    -tf 1 -ns 4 -j 4 \
    -interactionRate 500000 -run 302000 -seed 42 2>&1 | tail -5
ls -lh workflow.json
```

> For official productions, put the settings in an ini file (`[GeneratorHybrid]` / `configFile = ...`) and use `-gen hybrid -ini /path/to/file.ini`.

Look at the tasks:

```bash
${O2DPG_ROOT}/MC/bin/o2_dpg_workflow_runner.py -f workflow.json --list-tasks | head -60
```

### 2c. Run the workflow

Step 1: generation and transport only (few minutes).

```bash
cd $EX2
time ${O2DPG_ROOT}/MC/bin/o2_dpg_workflow_runner.py -f workflow.json -tt sgnsim \
     --cpu-limit 4 --mem-limit 14000 --stdout-on-failure > runner_sim.log 2>&1
tail -40 runner_sim.log
```

Step 2: continue up to the AOD. Finished tasks are **not** run again (checkpointing). It takes 15–30 minutes, so run it in the background and follow the log. You can keep working in another shell, or log out of a `screen`/`tmux` session.

```bash
cd $EX2
nohup ${O2DPG_ROOT}/MC/bin/o2_dpg_workflow_runner.py -f workflow.json -tt aod \
      --cpu-limit 4 --mem-limit 14000 --stdout-on-failure > runner_aod.log 2>&1 &
tail -f runner_aod.log        # Ctrl-C leaves tail, the job keeps running
```

While it runs: every task writes its own log (`tf1/sgnsim_1.log`, `tf1/tpcdigi_1.log`, …) and `pipeline_metric_*.log` holds CPU and memory of each task.

> **If a task fails** (`... had nonzero exit code`) the runner prints the log of the failing task at the end. Common causes: no token, missing `/usr/bin/time`, too small `/dev/shm`, a work directory mounted `noexec` (check with `findmnt -no OPTIONS --target $PWD`), not enough memory (lower `--cpu-limit` and `-j`).
>
> Optional: the new modular runner is selected with `ALIEN_O2DPG_WORKFLOW_RUNNER=new` and offers `--scheduler-policy timeframe|critical-path|best-fit`.

### 2d. Look at the AOD

When the runner prints `Pipeline done success`:

```bash
cd $EX2
root -l -b -q "$SIMTUT_PROJECT/macros/aodMcSummary.C(\"AO2D.root\",4122)"
```

**Questions**
1. The hybrid generator stores which entry of the JSON produced each event as the `subGeneratorId` of the MC collision. Which ID is the plain `pythia8pp` and which is the cocktail?
2. How many Λc⁺ per collision does each ID have? Can you tell the 5 injected Λc⁺ apart from the natural Pythia8 production? (In an analysis: `mcCollision.getSubGeneratorId()`.)
3. Change `"fractions"` to `[3, 1]` and rerun from the generation step (`--rerun-from sgngen`). How does the Λc⁺ yield change?

---

## Exercise 3: anchored MC with an external generator

An **anchored MC** reproduces the conditions of a real data-taking run: filling scheme, active detectors, interaction rate, calibrations and reconstruction settings of a given pass.

The steering script `${O2DPG_ROOT}/MC/run/ANCHOR/anchorMC.sh` is configured **only through environment variables**, the same ones the GRID sets from the JDL. It:
1. finds the timestamp of the requested slice (`SPLITID`/`PRODSPLIT`) of the run;
2. derives the interaction rate and the active detectors for that time;
3. fetches the reconstruction configuration of the pass;
4. creates the workflow (`o2dpg_sim_workflow_anchored.py`) and runs it up to the AOD.

**Generator**: an official PWGHF **gap-triggered** configuration, an *external* generator derived from Pythia8 and configured with an ini file. Every 3rd event contains a cc̄ or bb̄ pair in |y| < 1.5; the others are minimum-bias "gap" events. The type of each event is stored as the `subGeneratorId` of the MC collision: **0 = gap, 4 = cc̄-triggered, 5 = bb̄-triggered**.

### 3a. The generator configuration

```bash
cat ${O2DPG_MC_CONFIG_ROOT}/MC/config/PWGHF/ini/GeneratorHF_D2H_ccbar_and_bbbar_gap3.ini
```

### 3b. The steering script

Anchoring to **run 535069** (pp 13.6 TeV, LHC23f, pass `apass2`), kept small: 1 timeframe, 6 signal events, QC disabled.

```bash
cat $SIMTUT_PROJECT/config/anchorHF.sh
```

The number of cores and workers can be changed from the shell (`ALIEN_JDL_CPULIMIT`, default 4, and `NWORKERS`, default 2); the number of signal events with `NSIGEVENTS`, the slice with `SPLITID`.

### 3c. Run it

About 30–45 minutes on 4 cores, so in the background:

```bash
cd $EX3
nohup bash $SIMTUT_PROJECT/config/anchorHF.sh > anchor.log 2>&1 &
tail -f anchor.log
```

The first part of the log shows the anchoring decisions:

```bash
grep -m20 -iE 'timestamp|interaction ?rate|detectors|colliding|SOR|EOR' anchor.log
```

**Questions**
1. Which **interaction rate** was used? Which **detectors** are in the workflow?
2. Which **timestamp** was chosen? How does it relate to `SPLITID=50` of `PRODSPLIT=100`?
3. (After the run) change `SPLITID` (e.g. `SPLITID=10`, exporting it after sourcing a copy of the script). Do the timestamp and interaction rate change?

### 3d. Look at the AOD

```bash
cd $EX3
root -l -b -q "$SIMTUT_PROJECT/macros/aodMcSummary.C(\"AO2D.root\",421)"
```

How many MC collisions are **gap** events (`subGeneratorId` 0), and how many are **cc̄- (4) or bb̄-triggered (5)**? Is about 1 in 3 events triggered? Compare the number of D⁰ per collision in the gap and in the triggered events. Try other species: D⁺ 411, Λc⁺ 4122, B⁺ 521. With ~6 events per job, some species may not appear at all.

### 3e. (Optional) Submit the same script to the GRID

The script runs on the GRID without changes. `grid_submit.sh` sets `ALIEN_O2DPG_GRIDSUBMIT_PRODSPLIT` and `ALIEN_O2DPG_GRIDSUBMIT_SUBJOBID`, so each subjob anchors to a different slice of the run. On the GRID use 8 cores (`ALIEN_JDL_CPULIMIT=8`, `NWORKERS=8`) and a validated `MC-prod` release.

```bash
mkdir -p $SIMTUT_DIR/ex3_grid && cd $SIMTUT_DIR/ex3_grid
$O2DPG_ROOT/GRID/utils/grid_submit.sh --script $SIMTUT_PROJECT/config/anchorHF.sh --jobname anchorHFtutorial \
   --outputspec '*.log@disk=1','*.root@disk=2' \
   --packagespec 'VO_ALICE@O2PDPSuite::MC-prod-2026-v14-1' --prodsplit 4 --wait --fetch-output
```

Follow the jobs on [MonALISA](https://alimonitor.cern.ch). The line `**** Pipeline done success (global_runtime : …)` in the job logs gives the CPU time per job, the basis of the resource estimate for an official production.

> **2-tag mode**: to generate with a new release but reconstruct with the release of the async pass, add `export ALIEN_JDL_O2DPG_ASYNC_RECO_TAG="VO_ALICE@O2PDPSuite::<async tag>"` to the script.

---

## Keep your results

```bash
mkdir -p ~/simtutorial_results && cp -r $EX1/*.svg $EX1/*_Kine.root $EX2/AO2D.root $EX3/AO2D.root ~/simtutorial_results/
```

(`/tmp` is not permanent: copy what you need to your home or EOS.)

## Troubleshooting

| Symptom | Fix |
|---|---|
| `o2-sim: command not found` | the O2 environment is not loaded in this shell (section 2) |
| `TGrid::Connect returned nullptr`, `No certificate filename provided!` | no valid token: `alien-token-init`, then `alien-token-info` |
| `... had nonzero exit code` on every workflow task | `/usr/bin/time` is missing (install `time`), or the work directory is `noexec` |
| shared-memory errors in workflow tasks | `/dev/shm` too small: `export SHMSIZE=<bytes>` smaller than `/dev/shm` (`env.sh` does it) |
| out-of-memory kills | lower `-j` and `--cpu-limit`; the full workflow wants about 16 GB |
| slow / odd I/O errors on lxplus | work directory is on AFS/EOS: use `/tmp` (`SIMTUT_DIR`) |
| more details on token errors | `ALIENPY_DEBUG=1 alien-token-init`, then read `~/alien_py.log` |

Questions: Mattermost `O2 simulation` / `O2DPG`; docs at <https://aliceo2group.github.io/simulation/>.
