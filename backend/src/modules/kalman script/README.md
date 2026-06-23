# Scrap Optimisation

Flask-based application for:
- Kalman Filter-based scrap chemistry prediction (`Cu`, `Ni`, `Sn`, `Cr`, `P`)
- Heat-wise scrap mix optimization using PuLP + CBC solver
- Web UI flow for uploading HeatQuery files, running model prediction, and viewing recommendation output

## What this project does

1. Accepts plant heat data (`HeatQuery_All_*`) and chemistry data (`HeatQuery_Chemistry_*`)
2. Runs Kalman Filter updates to estimate scrap-wise chemistry contribution
3. Saves prediction outputs (overall + per heat + plots)
4. Runs optimization to suggest scrap quantities that meet chemistry and process constraints at lower cost
5. Returns recommendation tables (scrap mix, chemistry, actual vs suggested cost)

## Tech stack

- Python 3.x
- Flask
- Pandas / NumPy / SciPy / scikit-learn
- PuLP + bundled CBC solver (`solver/cbc.exe`)
- Matplotlib

## Repository structure

```text
ScrapOptimisation/
  app.py                                  # Flask app + API routes + UI serving
  kf_runner.py                            # KF orchestration wrapper
  Kalman_Scrap_Chemistry_Prediction.py    # Kalman filter pipeline + result exports
  run_optimization.py                     # Optimization logic and heat-wise processing
  test.py                                 # Script mode example (without UI)
  requirements.txt
  templates/index.html                    # Web UI
  static/                                 # UI assets
  Uploads/                                # Reference/config inputs used by pipeline
  outputs/                                # Generated outputs
  solver/cbc.exe                          # MILP solver used by PuLP
```

## Prerequisites

- Windows environment (current project setup includes Windows solver binary)
- Python and pip installed
- `solver/cbc.exe` present (already included in this repo)

## Installation

From project root:

```bash
pip install -r requirements.txt
```

## Run the app

```bash
python app.py
```

App starts on:
- `http://127.0.0.1:5000`

## UI workflow

1. Upload two files in this sequence:
   - `HeatQuery_All_*` (`.xlsx` or `.csv`)
   - `HeatQuery_Chemistry_*` (`.xlsx` or `.csv`)
2. Select:
   - Target chemistry (`ALL`, `Cu`, `Cr`, `Ni`, `Sn`, `P`)
   - Number of heats pass
3. Click **Run Model** (Kalman prediction)
4. Click **Run Recommendation** and upload recommendation input workbook (`.xlsx`)

## Required files and expected format

### 1) HeatQuery files (uploaded in UI)

- `HeatQuery_All_*`:
  - Main heat/scrap process input
  - Must contain columns required by `Uploads/Scrap_Chem_Input_Variables.xlsx` (`Feature_Variables` list)
- `HeatQuery_Chemistry_*`:
  - Must contain columns:
    - `HeatName`
    - `Chem`
    - `AppliedTime`
    - selected target chemistry column (`Cu` / `Ni` / `Sn` / `Cr` / `P`)
  - Only `Chem == LMF` rows are used

### 2) Recommendation input workbook (uploaded after Run Model)

- Excel only (`.xlsx`)
- Must include sheets:
  - `Input`
  - `Target`
  - `Parameters`

### 3) Reference/config files (must exist in `Uploads/`)

- `Scrap_Cost_Chemistry_Limits.xlsx`
  - Used for scrap type mapping and chemistry min/max limits
  - Must include columns: `Scrap Type`, `Scrap Type Ref`
- `CHG_Mapping_Ref.xlsx`
  - CHG reference mapping used in heat-wise processing
- `Scrap_Chem_Input_Variables.xlsx`
  - Must include column: `Feature_Variables`
  - Controls which columns are required from HeatQuery input
- `Recom_Scrap_Input_3 1.xlsx`
  - Template workbook used while building per-heat recommendation output

## Outputs generated

Generated under `outputs/` (names depend on target chemistry and heat id):

- Kalman prediction:
  - `KF_<CHEM>_Prediction.xlsx`
  - `KF_<CHEM>_Prediction_Heat_<HEATID>.xlsx`
  - `pred_vs_actual_<CHEM>.png`
- Scrap coefficient prediction:
  - `KF_Scrap_Type_Predictions_<CHEM>.xlsx` (or `.csv` when input is csv)
  - `KF_Scrap_Type_Predictions_<CHEM>_Heat_<HEATID>.xlsx` (or `.csv`)
- Heat-wise intermediate and final outputs:
  - `Input_with_KF_<CHEM>_<HEATID>.xlsx` (or `.csv`)
  - `Scrap_Optimization_Output_<HEATID>.xlsx` (or `.csv`)
- Additional per-heat workbook:
  - `KF_Scrap_Type_Predictions_<HEATID>.xlsx`

## API routes (Flask)

- `GET /` - UI page
- `POST /upload` - upload `HeatQuery_All_*` + `HeatQuery_Chemistry_*`
- `POST /run` - run Kalman model (`target_chem`, `numb_heats_pass`)
- `POST /run_recommendation` - run recommendation from input workbook

## Running without UI (script mode)

Use `test.py` as reference:

```bash
python test.py
```

This runs Kalman process for all configured chemistries and writes outputs to `Outputs2/`.

## Common issues and fixes

- **"Please upload both files" / naming errors**
  - Ensure both HeatQuery files are uploaded and names start with:
    - `HeatQuery_All_`
    - `HeatQuery_Chemistry_`

- **"Scrap_Chem_Input_Variables.xlsx not found"**
  - Place file in `Uploads/`

- **"Missing columns in input data..."**
  - Add missing columns listed in `Feature_Variables` sheet

- **"Input Excel must contain 'Target' and 'Parameters' sheets"**
  - Recommendation input workbook must include all required sheets (`Input`, `Target`, `Parameters`)

- **"CBC solver not found"**
  - Confirm `solver/cbc.exe` exists

## Notes

- The app cleans old model output files in `outputs/` before a new model run.
- File/folder names are resolved for both Python script mode and packaged/frozen execution mode.
- Existing `requirements.txt` includes extra tooling/notebook packages; for deployment, you may later create a minimal runtime requirements file.
