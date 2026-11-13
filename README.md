# ALICE Run 3 simulation hands-on on SWAN

A SWAN project for the simulation hands-on of the ALICE Analysis tutorial (November 2026).
Everything runs in a [SWAN](https://swan.cern.ch) session: participants need only a browser, a CERN account and an ALICE grid certificate.

| Notebook | Content |
|---|---|
| `00_setup.ipynb` | Check the session, load O2sim from CVMFS, create the AliEn token |
| `01_o2sim_basics.ipynb` | Exercise 1 — simplest `o2-sim` runs: Pythia8 pp, generator-only, fewer modules, Λc⁺ box gun |
| `02_hybrid_workflow.ipynb` | Exercise 2 — O2DPG workflow up to the AOD with the hybrid generator (plain + cocktail in one JSON) |
| `03_anchored_external.ipynb` | Exercise 3 — anchored MC (LHC23f run 535069) with the PWGHF gap-triggered external generator, optional GRID submission |

### 1. Start a SWAN session

Go to <https://swan.cern.ch> and choose:

| Setting | Value |
|---|---|
| Software stack | the latest default LCG release |
| Platform | AlmaLinux 9 |
| Number of cores | **4** |
| Memory | **16 GB** |
| Environment script | *(empty)* |

### 2. Get the project

Download the project from git:
*SWAN file browser → "Download project from git"* with the URL: https://github.com/jackal1-66/SimulationTutorial26

### 3. Grid certificate

Put your certificate in CERNBox: `~/.globus/usercert.pem` and `~/.globus/userkey.pem`.
You must be registered in the ALICE VO.

### 4. Run the notebooks in order

Start with `00_setup.ipynb`. The AliEn token is created in a SWAN terminal with `bash <project>/o2token`, so do this before starting the first notebook.

## How it works

The SWAN Python kernel uses the LCG software stack, which has its own ROOT and Python. O2 brings different versions, and mixing them in one process breaks both.
So the notebooks never load O2 into the kernel. `from swan_env import *` (the first cell of every notebook) **redefines the `%%bash` cell**: the cell is written to a script and run through the wrapper **`o2exec`**, which gives live output. Participants just write `o2-sim ...` or `root ...` in `%%bash` cells. `o2exec` can also be used directly, e.g. in a terminal:

```bash
o2exec o2-sim -n 5 -g pythia8pp
o2exec bash -c '$O2DPG_ROOT/MC/bin/o2dpg_sim_workflow.py ...'
```

`o2exec`:
- starts the command with a clean environment (`env -i`) and loads `VO_ALICE@O2sim::<tag>` with `alienv` from `/cvmfs/alice.cern.ch`;
- keeps only `HOME`, `USER`, the certificate/token variables and a few tutorial variables;
- if `/usr/bin/time` is missing (as it is unfortunately on SWAN), points `O2_ROOT` to an overlay of the O2 installation whose `share/scripts/jobutils2.sh` uses `gnutime.py`. O2's `jobutils2.sh` runs every O2DPG workflow task through a hardcoded `/usr/bin/time`, so without this every task fails with `... had nonzero exit code`;
- pins `TMPDIR=/tmp`, so the AliEn token created in the terminal (`/tmp/tokencert_<uid>.pem`) is found by the notebooks;
- loads silently (set `O2EXEC_VERBOSE=1` to see the module list) and reports loading errors;
- sets `SHMSIZE` to 3/4 of `/dev/shm`. O2DPG asks DPL for a 50 GB shared-memory segment by default, which does not fit in a container.

The tag is defined once in `swan_env.py` (`O2SIM_TAG`). The O2sim meta-package contains O2, O2DPG, O2Physics, QualityControl and the generators.

`swan_env.py` (imported by every notebook) also:
- defines the working directory `SIMTUT_DIR`. Simulations run on the session local disk, because CERNBox/EOS is slow for the many small files of a workflow. The O2DPG runner executes scripts in the work directory, so the directory must allow that. `swan_env` tests `/tmp/$USER/simtutorial`, then `/var/tmp/$USER/simtutorial`, then `~/simtutorial_work` (CERNBox), and uses the first one that works. This is needed because SWAN may mount `/tmp` `noexec`, which makes every workflow task fail with `chmod +x ... had nonzero exit code`;
- copies `macros/`, `config/` and `o2exec` to `$SIMTUT_DIR/project` (local disk) every time a notebook starts, and points `SIMTUT_PROJECT` and `PATH` to that copy. Programs inside `o2exec` then never need to read CERNBox, and executable bits dropped by SWAN uploads don't matter;
- adds helpers: `start()` / `status()` / `stop()` to run long jobs in the background (they survive an interrupted cell), and `show()` to display plots.

Results are copied to `~/simtutorial_results/` on CERNBox at the end of each exercise, because `/tmp` is wiped when the session ends.

## Files

```
SWAN/
├── README.md
├── o2exec                      # O2 environment wrapper
├── o2token                     # creates the AliEn token (run in a SWAN terminal; asks the certificate password)
├── gnutime.py                  # stand-in for /usr/bin/time (missing on SWAN), used by o2exec
├── swan_env.py                 # common notebook setup + helpers
├── 00_setup.ipynb … 03_anchored_external.ipynb
├── config/
│   ├── hybrid_pp_cocktail.json # pythia8pp  |  cocktail(pythia8pp + 5 Λc⁺ boxgen), fractions 1:1
│   └── anchorHF.sh             # anchorMC.sh steering, external PWGHF gap-triggered generator
└── macros/
    ├── kineOverview.C          # PDG codes + production vertex from o2sim_Kine.root (PNG)
    ├── kineDaughters.C         # per-event count and decay products of a species
    └── aodMcSummary.C          # MC collisions per sub-generator ID + species count in an AO2D
```
