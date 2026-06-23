import pandas as pd
import numpy as np
# from gurobipy import Model, GRB, quicksum
import io
import os
from pulp import *
from pathlib import Path
import sys
from pulp import COIN_CMD
import json
from datetime import datetime
from io import BytesIO
import re
import matplotlib.pyplot as plt
from helper_functions import *


def _first_existing(paths):
    for p in paths:
        p = Path(p)
        if p.exists():
            return p
    return None


def resolve_kf_prediction_path(base_dir: Path, target_chem: str):
    """Undated KF prediction files first, then YYYYMMDD fallback."""
    base_dir = Path(base_dir)
    date_str = datetime.now().strftime("%Y%m%d")
    candidates = [
        base_dir / f"KF_{target_chem}_Prediction.csv",
        base_dir / f"KF_{target_chem}_Prediction.xlsx",
        base_dir / f"KF_{target_chem}_Prediction_{date_str}.csv",
        base_dir / f"KF_{target_chem}_Prediction_{date_str}.xlsx",
    ]
    return _first_existing(candidates)


def resolve_kf_scrap_coef_path(base_dir: Path, target_chem: str):
    """Undated aggregate scrap-coef file first, then dated fallback."""
    base_dir = Path(base_dir)
    date_str = datetime.now().strftime("%Y%m%d")
    candidates = [
        base_dir / f"KF_Scrap_Type_Predictions_{target_chem}.csv",
        base_dir / f"KF_Scrap_Type_Predictions_{target_chem}.xlsx",
        base_dir / f"KF_Scrap_Type_Predictions_{target_chem}_{date_str}.csv",
        base_dir / f"KF_Scrap_Type_Predictions_{target_chem}_{date_str}.xlsx",
    ]
    return _first_existing(candidates)


def _update_kf_heat_workbook_sheets(
    output_dir: Path,
    heat_id,
    target_sheet: pd.DataFrame,
    param_sheet: pd.DataFrame,
    input_sheet_df: pd.DataFrame = None,
):
    """Update Input/Target/Parameters sheets in per-heat KF workbook."""
    heat_wb_path = Path(output_dir) / f"KF_Scrap_Type_Predictions_{int(heat_id)}.xlsx"
    if not heat_wb_path.exists():
        print(f"WARNING: KF heat workbook not found, skipping sheet update: {heat_wb_path}")
        return

    try:
        def _norm_scrap_name(x):
            return " ".join(str(x).strip().split())

        def _strip_chg_prefix(x):
            t = str(x).strip()
            if t.upper().startswith("CHG"):
                t = t[3:].lstrip("- ").lstrip()
            return t

        xl = pd.ExcelFile(heat_wb_path)
        book = {sn: pd.read_excel(heat_wb_path, sheet_name=sn) for sn in xl.sheet_names}

        if input_sheet_df is not None and not input_sheet_df.empty and "Input" in book:
            inp = book["Input"].copy()
            if (
                "Max Quantity available (NT)" in inp.columns
                and "Scrap Type" in input_sheet_df.columns
                and "Max Quantity available (NT)" in input_sheet_df.columns
            ):
                src = input_sheet_df[["Scrap Type", "Max Quantity available (NT)"]].copy()
                src["__scrap_key"] = src["Scrap Type"].map(_strip_chg_prefix).map(_norm_scrap_name)
                src = src.drop_duplicates(subset=["__scrap_key"], keep="last")
                src_map = pd.Series(src["Max Quantity available (NT)"].values, index=src["__scrap_key"]).to_dict()

                key_col = "Scrap_Type_New" if "Scrap_Type_New" in inp.columns else ("Scrap Type" if "Scrap Type" in inp.columns else None)
                if key_col is not None:
                    inp_keys = inp[key_col].map(_strip_chg_prefix).map(_norm_scrap_name)
                    mapped = inp_keys.map(src_map)
                    # Reset full column to zero before applying mapped updates.
                    inp["Max Quantity available (NT)"] = 0
                    inp.loc[mapped.notna(), "Max Quantity available (NT)"] = mapped[mapped.notna()]
                    book["Input"] = inp
                else:
                    print(f"WARNING: No scrap key column found in Input sheet for {heat_wb_path}")

        book["Target"] = target_sheet.copy()
        book["Parameters"] = param_sheet.copy()

        with pd.ExcelWriter(heat_wb_path, engine="openpyxl") as writer:
            for sheet_name, sheet_df in book.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"Updated Input/Target/Parameters in: {heat_wb_path}")
    except Exception as e:
        print(f"WARNING: Could not update workbook sheets for {heat_wb_path}: {e}")


def run_optimization_pulp(df_input, target_df, param_df, return_json=False):

    print("INSIDE run_optimization_pulp")

    print("Sum of Purchase cost Before: ", df_input['Purchase Cost'].sum())

    # -----------------------------
    # ADD THIS BLOCK HERE
    # -----------------------------
    if target_df is None or target_df.empty:
        raise ValueError("Target data required for optimization")

    if param_df is None or param_df.empty:
        raise ValueError("Parameter data required for optimization")

    input_scrap_name = df_input['Scrap Type']
    input_scrap_cost = df_input['Purchase Cost']
    print("Sum of Purchase cost After: ", df_input['Purchase Cost'].sum())
    input_scrap_max = df_input['Max Quantity available (NT)']
    input_scrap_min = df_input['Min Quantity To be Use (NT)']

    input_kwh = df_input['KWH']
    input_yield = df_input['Yield']
    input_flux_index = df_input['Flux and Carbon Index']
    input_chem_table = df_input[['C','Si','Mn','Cu','Cr','Ni','Sn','P','S','Mb','Fe']]

    # input_metalic_cost = input_scrap_cost / input_yield
    # input_power_cost   = input_kwh * 0.0504
    # input_flux_cost    = input_flux_index * 1.2 + 25
    # Input_total_cost   = input_metalic_cost + input_power_cost + input_flux_cost
    Input_total_cost = df_input['Total Yield + Power+ Flux Cost']

    # Fake constraint table for demonstration (replace with actual)
    target_df.index = target_df['Element']
    target_dict = target_df.to_dict(orient='index')

    n = len(input_scrap_name)

    # ---- Pulp Model ----
    m = LpProblem("Scrap_Optimization", LpMinimize)

    x = LpVariable.dicts("x", indices=range(n), lowBound=0, cat="Continuous")
    y = LpVariable.dicts("y", indices=range(n), lowBound=0, cat="Binary")

    # Objective function
    m += lpSum(Input_total_cost[i] * x[i] for i in range(n))

    # Constraints
    for i in range(n):
        m += x[i] <= input_scrap_max[i]
        m += x[i] >= input_scrap_min[i]

    total_qty = lpSum(x[i] for i in range(n))
    # m += total_qty >= 100000
    max_total_qty_per_heat = float(param_df.loc[param_df['Parameter']=='Total capacity per heat','Value'].values[0])
    m += total_qty >= max_total_qty_per_heat

    elements = input_chem_table.columns.tolist()
    for idx, element in enumerate(elements):
        input_chem_table[element] = input_chem_table[element].fillna(0)
        vec = input_chem_table[element].values

        # SKIP CONSTRAINT IF ALL ZERO
        if vec.sum() == 0:
            continue

        m += (lpSum(x[i] * vec[i] for i in range(n)) >= target_dict[element]['Min'] * total_qty)
        m += (lpSum(x[i] * vec[i] for i in range(n)) <= target_dict[element]['Max'] * total_qty)

    # Solve the model
    m.solve(get_cbc_solver(msg=False))
    # m.solve(GUROBI())

    print("Solver Status:", m.status)

    # ---- Export to Excel in memory ----
    output = io.BytesIO()
    output_json = {}

    if m.status == 1:
        result_df = pd.DataFrame({
            "Scrap Type": input_scrap_name,
            "Quantity Used in Pound": [x[i].value() for i in range(n)],
            "Cost in Dollar per Pound": Input_total_cost,
            "Total Cost Contribution in Dollar": [x[i].value() * Input_total_cost[i] for i in range(n)]
        })

        chemistry = {}
        for element in elements:
            vec = input_chem_table[element].values
            avg = sum(x[i].value() * vec[i] for i in range(n)) / sum(x[i].value() for i in range(n))
            chemistry[element] = avg * 100

        chemistry_df = pd.DataFrame(chemistry, index=["Achieved Chemistry"])

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            result_df.to_excel(writer, index=False, sheet_name="Scrap Mix")
            chemistry_df.to_excel(writer, sheet_name="Chemistry")

        output.seek(0)

        if return_json:
            output_json = {
                "scrap_mix": result_df.to_dict(orient="records"),
                "chemistry": chemistry_df.reset_index().to_dict(orient="records")
            }
    else:
        result_df = pd.DataFrame(['No Solution Found'], columns=['Result'])

        # ✅ ALWAYS CREATE CHEMISTRY SHEET
        chemistry_df = pd.DataFrame({'Message': ['No Chemistry Data']})

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            result_df.to_excel(writer, index=False, sheet_name="Scrap Mix")
            chemistry_df.to_excel(writer, sheet_name="Chemistry")

        output.seek(0)

        output_json = {
            "scrap_mix": result_df.to_dict(orient="records")
        }

    # m.dispose()
    if return_json:
        return output, output_json
    return output

def clean_col(col):
    col = str(col)
    col = col.replace('\xa0', ' ')   # remove hidden spaces
    col = col.strip()
    col = re.sub(r'\s+', ' ', col)
    return col


def _merge_chemistry_tracker(che_tracker_df: pd.DataFrame, current_df: pd.DataFrame) -> pd.DataFrame:
    """Accumulate per-scrap chemistry; latest `current_df` wins. Index alignment only—no merge suffix columns."""
    cur = current_df.drop_duplicates(subset=["Scrap Type"], keep="last")
    if cur.empty:
        return che_tracker_df.copy() if not che_tracker_df.empty else cur
    if che_tracker_df.empty:
        return cur.copy()
    base = che_tracker_df.drop_duplicates(subset=["Scrap Type"], keep="last")
    a = cur.set_index("Scrap Type")
    b = base.set_index("Scrap Type")
    return a.combine_first(b).reset_index()


def _apply_che_tracker_to_df(df: pd.DataFrame, che_tracker_df: pd.DataFrame) -> pd.DataFrame:
    """Overlay accumulated chemistry from tracker onto `df` by Scrap Type."""
    if che_tracker_df.empty:
        return df.copy()
    out = df.copy()
    t = che_tracker_df.drop_duplicates(subset=["Scrap Type"], keep="last").set_index("Scrap Type")
    for col in t.columns:
        print("t.columns: ", t.columns)
        if col == "Scrap Type":
            continue
        mapped = out["Scrap Type"].map(t[col])

        if col not in out.columns:
            out[col] = mapped
        else:
            out[col] = mapped.where(mapped.notna(), out[col])
    return out


# def _apply_target_tracker(target_sheet: pd.DataFrame, target_tracker_df: pd.DataFrame) -> pd.DataFrame:
def _apply_target_tracker(target_sheet: pd.DataFrame, target_tracker_df: pd.DataFrame, heat_id, original_data_reference_upld: pd.DataFrame, grade_spec_df: pd.DataFrame) -> pd.DataFrame:

    """Apply Min/Max overrides from in-memory target_tracker_df."""
    if target_tracker_df.empty:
        return target_sheet.copy()
    out = target_sheet.set_index("Element")
    tt = target_tracker_df.drop_duplicates(subset=["Element"], keep="last").set_index("Element")
    out = out.copy()
    for col in ("Min", "Max"):
        if col in tt.columns:
            out[col] = tt[col].combine_first(out[col])

    out = out.reset_index()

    print("out df beforeee: ", out.head())

    out = enforce_grade_spec_limits(heat_id, original_data_reference_upld, result_df=grade_spec_df, target_df=out)

    print("out df aftereee: ", out.head())

    # ---------------------------------------------------------
    # Restrict only selected elements
    # ---------------------------------------------------------
    restrict_elements = ["Cu"]   # example

    if restrict_elements:

        mask = ~out["Element"].isin(restrict_elements)

        out.loc[mask, "Min"] = 0
        out.loc[mask, "Max"] = 1

    print("out df last: ", out.head())

    return out.reset_index()


def _load_existing_target_base(output_dir: Path, heat_id, fallback_target_df: pd.DataFrame) -> pd.DataFrame:
    """Use existing per-heat workbook Target sheet as base; fallback to template target sheet."""
    base = fallback_target_df.copy().reset_index(drop=True)
    if "Element" not in base.columns:
        return base

    heat_wb_path = Path(output_dir) / f"KF_Scrap_Type_Predictions_{int(heat_id)}.xlsx"
    if not heat_wb_path.exists():
        return base

    try:
        existing_target = pd.read_excel(heat_wb_path, sheet_name="Target")
    except Exception as e:
        print(f"WARNING: Could not read existing Target sheet for {heat_wb_path}: {e}")
        return base

    if existing_target.empty or "Element" not in existing_target.columns:
        return base

    out = base.set_index("Element")
    existing = existing_target.drop_duplicates(subset=["Element"], keep="last").set_index("Element")
    out = out.copy()
    for col in ("Min", "Max"):
        if col in out.columns and col in existing.columns:
            out[col] = existing[col].combine_first(out[col])
    return out.reset_index()


def run_heatwise_optimization(
    df_input,
    target_chem,
    output_dir,
    mapping_file_path,
    kf_output_file_path,
    target_df,
    param_df,
    input_file_path,  # ADD THIS
    input_ext=".xlsx",
    numb_heats_pass=1,   # ✅ ADD THIS
    kf_coef_df=None,
    kf_pred_df=None,
):  
    print("INSIDE run_heatwise_optimization")

    # ✅ ADD HERE (inside function, top)
    first_actual_qty_df = None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # DEFINE PATHS (already in your code)
    # -----------------------------
    if getattr(sys, 'frozen', False):
        runtime_dir = Path(sys.executable).parent
        bundle_dir = Path(sys._MEIPASS)
    else:
        runtime_dir = Path(__file__).parent
        bundle_dir = Path(__file__).parent

    # -----------------------------
    # DEFINE VARIABLES FILE PATH
    # -----------------------------
    vars_file = (
        runtime_dir / "uploads" / "Scrap_Chem_Input_Variables.xlsx"
        if (runtime_dir / "uploads" / "Scrap_Chem_Input_Variables.xlsx").exists()
        else bundle_dir / "uploads" / "Scrap_Chem_Input_Variables.xlsx"
    )

    # -----------------------------
    # READ VARIABLE CONFIG FILE
    # -----------------------------
    if not vars_file.exists():
        raise FileNotFoundError("❌ Scrap_Chem_Input_Variables.xlsx not found in uploads folder")

    vars_df = pd.read_excel(vars_file)

    # Clean column names
    vars_df.columns = vars_df.columns.str.strip()

    # Extract required columns
    required_cols = (
    vars_df["Feature_Variables"]
    .dropna()
    .astype(str)
    .str.strip()
    )

    # -----------------------------
    # Grade Spec File Path
    # -----------------------------
    grade_spec_file = (
        runtime_dir / "uploads" / "Grade_Specifications.xlsx"
        if (runtime_dir / "uploads" / "Grade_Specifications.xlsx").exists()
        else bundle_dir / "uploads" / "Grade_Specifications.xlsx"
    )

    # -----------------------------
    # READ Grade Spec FILE
    # -----------------------------
    if not grade_spec_file.exists():
        raise FileNotFoundError(
            "❌ Grade_Specifications.xlsx not found in uploads folder"
        )

    grade_spec_df = clean_grade_spec_excel(grade_spec_file)

    # -----------------------------
    # 1. Read mapping file
    # -----------------------------
    mapping_df = pd.read_excel(mapping_file_path)

    if not {"Scrap Type", "Scrap Type Ref"}.issubset(mapping_df.columns):
        raise ValueError("Mapping file must contain 'Scrap Type' and 'Scrap Type Ref'")

    mapping_dict = dict(zip(mapping_df["Scrap Type Ref"], mapping_df["Scrap Type"]))

    #-----------------------------
    chg_mapping_path = mapping_file_path.parent / "CHG_Mapping_Ref.xlsx"
    chg_map_df = pd.read_excel(chg_mapping_path)
    #-----------------------------

    # -----------------------------
    # 2. Read KF output file
    # -----------------------------

    if kf_coef_df is not None and not kf_coef_df.empty:
        print("Using in-memory KF scrap coefficient dataframe")
        kf_df_raw = kf_coef_df.copy()
    else:
        # Read KF file based on format
        if kf_output_file_path is None:
            raise ValueError("KF scrap coefficient source missing (no in-memory dataframe and no file path)")
        if str(kf_output_file_path).lower().endswith(".csv"):
            print("The kf_df filename used: ", kf_output_file_path)
            kf_df_raw = pd.read_csv(kf_output_file_path)
        else:
            kf_df_raw = pd.read_excel(kf_output_file_path)
            print("The kf_df filename used: ", kf_output_file_path)

    # Remove duplicates
    kf_df_raw = kf_df_raw.drop_duplicates()
    kf_df = kf_df_raw.copy()

    # -----------------------------
    # 3. Rename CHG columns → Scrap Type
    # -----------------------------
    chg_cols = [c for c in kf_df.columns if c.startswith("CHG")]

    rename_map = {}
    for col in chg_cols:
        if col not in mapping_dict:
            raise ValueError(f"Mapping not found for column: {col}")
        rename_map[col] = mapping_dict[col]

    kf_df = kf_df.rename(columns=rename_map)

    # -----------------------------
    # 4. Validate input scrap types
    # -----------------------------
    input_scraps = df_input["Scrap Type"].tolist()

    available_scraps = set(rename_map.values())

    missing_scraps = [s for s in input_scraps if s not in available_scraps]

    if missing_scraps:
        print(f"WARNING: These scraps not found in KF output → will be filled with 0: {missing_scraps}")


    # -----------------------------
    # LOAD HEATQUERY FILE (ONCE)
    # -----------------------------
    if str(input_file_path).lower().endswith(".csv"):
        original_data_reference_upld = pd.read_csv(input_file_path)
        # original_data_reference.columns = [clean_col(c) for c in original_data_reference.columns]
    else:
        original_data_reference_upld = pd.read_excel(input_file_path)
        # original_data_reference.columns = [clean_col(c) for c in original_data_reference.columns]

    # -----------------------------
    # FILTER REQUIRED COLUMNS
    # -----------------------------
    missing_cols = [col for col in required_cols if col not in original_data_reference_upld.columns]

    if missing_cols:
        print(f"⚠️ Missing columns in input file: {missing_cols}")

    # Keep only available columns
    available_cols = [col for col in required_cols if col in original_data_reference_upld.columns]

    original_data_reference = original_data_reference_upld[available_cols]


    # In-memory only (no che_tracker_df.xlsx / target_tracker_df.xlsx)
    che_tracker_df = pd.DataFrame()
    target_tracker_df = pd.DataFrame(columns=["Element", "Min", "Max"])

    # -----------------------------
    # 5. Process per HeatID
    # -----------------------------
    for _, row in kf_df.iterrows():

        heat_id = int(row.get("HeatID"))

        df_copy = df_input.copy()

        # -----------------------------
        # FILTER ORIGINAL DATA FOR HEATID
        # -----------------------------
        heat_row_df = original_data_reference[
            original_data_reference["HeatID"] == heat_id
        ]

        if heat_row_df.empty:
            print(f"WARNING: HeatID {heat_id} not found in HeatQuery file")
            heat_row = pd.Series()
        else:
            heat_row = heat_row_df.iloc[0]

        # --------------------------------------------------------------------------------------------------------------------#
        # STEP (a): UPDATE PARAMETER SHEET VALUE
        # --------------------------------------------------------------------------------------------------------------------#

        chg_cols = [c for c in original_data_reference.columns if str(c).startswith("CHG")]

        total_chg_qty = 0
        for col in chg_cols:
            val = heat_row.get(col, 0)
            if pd.notna(val):
                total_chg_qty += float(val)

        total_chg_qty = int(total_chg_qty)

        param_df_updated = param_df.copy()

        param_df_updated.loc[
            param_df_updated['Parameter'] == 'Total capacity per heat',
            'Value'
        ] = total_chg_qty

        # --------------------------------------------------------------------------------------------------------------------#
        # STEP (b): UPDATE TARGET SHEET (MIN/MAX)
        # --------------------------------------------------------------------------------------------------------------------#

        target_df_updated = _load_existing_target_base(
            output_dir=output_dir,
            heat_id=heat_id,
            fallback_target_df=target_df,
        )

        # Read KF prediction workbook (undated name preferred; dated fallback)
        if kf_pred_df is not None and not kf_pred_df.empty:
            kf_pred_file = kf_pred_df.copy().drop_duplicates()
        else:
            try:
                if kf_output_file_path is None:
                    raise FileNotFoundError("KF prediction source missing (no in-memory dataframe and no file path)")
                base_dir = Path(kf_output_file_path).parent  # existing outputs folder

                kf_pred_path = resolve_kf_prediction_path(base_dir, target_chem)
                if kf_pred_path is None:
                    date_str = datetime.now().strftime("%Y%m%d")
                    raise FileNotFoundError(
                        f"KF prediction file not found for {target_chem} under {base_dir}. "
                        f"Expected KF_{target_chem}_Prediction.xlsx (or .csv), "
                        f"or dated KF_{target_chem}_Prediction_{date_str}.*"
                    )

                if kf_pred_path.suffix.lower() == ".csv":
                    kf_pred_file = pd.read_csv(kf_pred_path)
                else:
                    kf_pred_file = pd.read_excel(kf_pred_path)
                kf_pred_file = kf_pred_file.drop_duplicates()

            except Exception as e:
                raise ValueError(f"Error reading KF prediction file: {str(e)}")

        kf_row = kf_pred_file[kf_pred_file["HeatID"] == heat_id]

        # ============================================================
        # ✅ PLOT ONLY ON FIRST ITERATION + HEAT PASS = 1
        # ============================================================
        if _ == 0 and int(numb_heats_pass) == 1:

            print("📊 Generating plots...")

            try:
                # =====================================================
                # 📌 FILE 1: KF_{target_chem}_Prediction
                # =====================================================
                if kf_pred_df is not None and not kf_pred_df.empty:
                    df1 = kf_pred_df.copy()
                else:
                    base_dir = Path(kf_output_file_path).parent
                    file1_path = resolve_kf_prediction_path(base_dir, target_chem)
                    if file1_path is None:
                        raise FileNotFoundError(f"No KF prediction file for plots ({target_chem})")
                    if file1_path.suffix.lower() == ".csv":
                        df1 = pd.read_csv(file1_path)
                    else:
                        df1 = pd.read_excel(file1_path)

                df1 = df1.head(30)  # ✅ LIMIT TO 30 ROWS

                # -------------------------------
                # ✅ STD Calculation
                # -------------------------------
                std_val = round(df1["Error_rate_residual"].std(ddof=0), 3)

                # -------------------------------
                # ✅ Upper / Lower bounds
                # -------------------------------
                pred_col = f"{target_chem}_predicted"
                lab_col = f"{target_chem}_lab"

                df1["upper_bound"] = df1[pred_col] + 3 * std_val
                df1["lower_bound"] = df1[pred_col] - 3 * std_val

                # -------------------------------
                # ✅ Plot
                # -------------------------------
                plt.figure(figsize=(12,6))

                plt.plot(df1[lab_col].values, label=f"{target_chem}_lab", linewidth=2)
                plt.scatter(range(len(df1)), df1[pred_col], color="green", label=f"{target_chem}_predicted")

                plt.plot(df1["upper_bound"], linestyle="dashed", label="Upper")
                plt.plot(df1["lower_bound"], linestyle="dashed", label="Lower")

                plt.title(target_chem)
                plt.legend()
                plt.grid(True)

                # plot_path = output_dir / f"{target_chem}_Prediction_Plot.png"
                # plt.savefig(plot_path)
                plt.close()

                # print(f"✅ Plot saved: {plot_path}")


                # =====================================================
                # 📌 FILE 2: KF_Scrap_Type_Predictions
                # =====================================================
                if kf_coef_df is not None and not kf_coef_df.empty:
                    df2 = kf_df_raw.copy()
                else:
                    base_dir = Path(kf_output_file_path).parent
                    file2_path = resolve_kf_scrap_coef_path(base_dir, target_chem)
                    if file2_path is None:
                        raise FileNotFoundError(f"No KF scrap-type coef file for plots ({target_chem})")
                    if file2_path.suffix.lower() == ".csv":
                        df2 = pd.read_csv(file2_path)
                    else:
                        df2 = pd.read_excel(file2_path)

                df2 = df2.head(30)  # ✅ LIMIT

                # Identify CHG columns (first 5)
                chg_cols_new = [c for c in df2.columns if c.startswith("CHG")][:5]

                for col in chg_cols_new:

                    std_val = round(df2[col].std(ddof=0), 3)

                    df2[f"{col}_upper"] = df2[col] + 3 * std_val
                    df2[f"{col}_lower"] = df2[col] - 3 * std_val

                    # -------------------------------
                    # Plot per CHG
                    # -------------------------------
                    plt.figure(figsize=(12,6))

                    plt.plot(df2[col].values, label=col, linewidth=2)
                    plt.plot(df2[f"{col}_upper"], linestyle="dashed", label="Upper")
                    plt.plot(df2[f"{col}_lower"], linestyle="dashed", label="Lower")

                    plt.title(col)
                    plt.legend()
                    plt.grid(True)

                    # plot_path = output_dir / f"{col}_Prediction_Plot.png"
                    # plt.savefig(plot_path)
                    plt.close()

                    # print(f"✅ Plot saved: {plot_path}")

            except Exception as e:
                print(f"⚠️ Plot generation failed: {str(e)}")

        elif _ == 0:
            print("⚠️ Plots will only be generated when Number of Heats Pass = 1")

        # ============================================================

        if not kf_row.empty:
            kf_row = kf_row.iloc[0]

            # HANDLE ALL vs SINGLE
            if target_chem == "ALL":
                chem_list = ['Cu', 'Ni', 'Sn', 'Cr', 'P']
            else:
                if not che_tracker_df.empty:
                    existing_chems = [c for c in che_tracker_df.columns if c != "Scrap Type"]
                    chem_list = list(dict.fromkeys(existing_chems + [target_chem]))
                else:
                    chem_list = [target_chem]

            for chem in chem_list:
                # est_col = f"{target_chem}_estimated"
                est_col = f"{chem}_estimated"

                if est_col in kf_row and pd.notna(kf_row[est_col]):
                    est_val = float(kf_row[est_col])

                    min_val = 0.7 * est_val
                    max_val = 1.3 * est_val

                    target_df_updated.loc[
                        target_df_updated['Element'] == chem, 'Min'
                    ] = min_val

                    target_df_updated.loc[
                        target_df_updated['Element'] == chem, 'Max'
                    ] = max_val

                    # ✅ STORE CURRENT CHEM MIN/MAX
                    current_target = target_df_updated[
                        target_df_updated["Element"] == chem
                    ][["Element", "Min", "Max"]]

                    if target_tracker_df.empty:
                        target_tracker_df = current_target
                    else:
                        target_tracker_df = pd.concat([target_tracker_df, current_target], ignore_index=True)

                    # ✅ REMOVE DUPLICATES (keep latest)
                    target_tracker_df = target_tracker_df.drop_duplicates(subset=["Element"], keep="last")

        # --------------------------------------------------------------------------------------------------------------------#
        # STEP (c): UPDATE MAX QUANTITY USING CHG
        # --------------------------------------------------------------------------------------------------------------------#

        MULTIPLIER = 5

        # -----------------------------
        # Build CHG → Scrap Type mapping dict
        # -----------------------------
        chg_to_scrap = {}

        for _, r in chg_map_df.iterrows():
            chg_col = str(r.iloc[0]).strip()
            scrap = str(r.iloc[1]).strip()

            if chg_col not in chg_to_scrap:
                chg_to_scrap[chg_col] = []

            chg_to_scrap[chg_col].append(scrap)

        # -----------------------------
        # Build Scrap Type → total CHG qty (SUM multiple)
        # -----------------------------
        scrap_qty_dict = {}

        for chg_col in chg_cols:
            val = heat_row.get(chg_col, 0)

            if pd.notna(val):
                val = float(val)

                if chg_col in chg_to_scrap:
                    for scrap in chg_to_scrap[chg_col]:

                        if scrap not in scrap_qty_dict:
                            scrap_qty_dict[scrap] = 0

                        scrap_qty_dict[scrap] += val

        # -----------------------------
        # Update df_copy + capture actual qty
        # -----------------------------
        actual_qty_records = []

        for idx, row_df in df_copy.iterrows():
            scrap_type = row_df['Scrap Type']

            actual_qty = scrap_qty_dict.get(scrap_type, 0)
            max_qty = actual_qty * MULTIPLIER

            df_copy.at[idx, 'Max Quantity available (NT)'] = max_qty

            actual_qty_records.append({
                "Scrap Type": scrap_type,
                "Actual Quantity Used": actual_qty
            })

        # -----------------------------
        # CREATE NEW DF FOR MERGE
        # -----------------------------
        actual_qty_df = pd.DataFrame(actual_qty_records)

        # Add Purchase Cost
        actual_qty_df = actual_qty_df.merge(
            df_copy[['Scrap Type', 'Purchase Cost']],
            on='Scrap Type',
            how='left'
        )

        print("The actual_qty_df purchase cost: ", actual_qty_df['Purchase Cost'].sum())

        # Remove duplicates (important)
        actual_qty_df = actual_qty_df.drop_duplicates()

        # -----------------------------
        # ✅ STORE ONLY FIRST HEAT DATA
        # -----------------------------
        # if first_actual_qty_df is None:
        first_actual_qty_df = actual_qty_df.copy()

        # -----------------------------
        # Fill target_chem column
        # -----------------------------
        if target_chem == "ALL":
            chem_list = ['Cu', 'Ni', 'Sn', 'Cr', 'P']
        else:
            chem_list = [target_chem]


        for chem in chem_list:
            for scrap in input_scraps:
                if scrap in row:
                    val = row.get(scrap, 0)

                    if pd.isna(val):
                        val = 0

                    df_copy.loc[df_copy["Scrap Type"] == scrap, chem] = val
                else:
                    df_copy.loc[df_copy["Scrap Type"] == scrap, chem] = 0.0


        # ✅ EXTRACT ONLY CURRENT CHEM COLUMN
        current_cols = ["Scrap Type"] + chem_list
        current_df = df_copy[current_cols].copy()

        che_tracker_df = _merge_chemistry_tracker(che_tracker_df, current_df)
        df_to_save = _apply_che_tracker_to_df(df_copy, che_tracker_df)

        # -----------------------------
        # SAVE INTERMEDIATE INPUT (for validation) #Use for validation checking
        # -----------------------------
        # input_filename = f"Input_with_KF_{target_chem}_{heat_id}.xlsx"
        # input_save_path = output_dir / input_filename
        #
        # if input_ext == ".csv":
        #     input_save_path = output_dir / f"Input_with_KF_{target_chem}_{heat_id}.csv"
        #     df_to_save.to_csv(input_save_path, index=False)
        # else:
        #     input_save_path = output_dir / f"Input_with_KF_{target_chem}_{heat_id}.xlsx"
        #     df_to_save.to_excel(input_save_path, index=False)

        # target_sheet = _apply_target_tracker(target_df_updated.copy(), target_tracker_df)
        target_sheet = _apply_target_tracker(target_df_updated.copy(), target_tracker_df,  heat_id,  original_data_reference_upld, grade_spec_df)
        print("Target sheet after applying tracker and grade spec limits: ", target_sheet.head())
        target_sheet = target_sheet.drop(columns=["index"]).reset_index(drop=True)

        param_sheet = param_df_updated.copy()

        _update_kf_heat_workbook_sheets(
            output_dir=output_dir,
            heat_id=heat_id,
            target_sheet=target_sheet,
            param_sheet=param_sheet,
            input_sheet_df=df_to_save,
        )

        # Save all 3 sheets
        # with pd.ExcelWriter(input_save_path, engine="xlsxwriter") as writer:
        #     df_to_save.to_excel(writer, index=False, sheet_name="Input")       # ✅ renamed
        #     target_sheet.to_excel(writer, index=False, sheet_name="Target") # ✅ copy
        #     param_sheet.to_excel(writer, index=False, sheet_name="Parameters") # ✅ copy

        # # ✅ Decide what to pass to optimizer
        if target_chem == chem_list[-1]:
            print("I'M INSIDE THE LOOP")
            # df_final = pd.read_excel(input_save_path, sheet_name="Input")
            # print("The filename for testing: ", input_save_path)
            df_for_optimization = df_to_save.copy()
        else:
            df_for_optimization = df_copy

        # -----------------------------
        # 6. Run optimization
        # -----------------------------
        print("Selected Target Chem", target_chem)
        print(df_for_optimization["Cu"].sum(), df_for_optimization["Cr"].sum(), df_for_optimization["P"].sum())
        output_excel = run_optimization_pulp(df_for_optimization, target_sheet, param_sheet)

        if input_ext == ".csv":
            output_path = output_dir / f"Scrap_Optimization_Output_{int(heat_id)}.csv"
            

            output_excel.seek(0)
            excel_copy = BytesIO(output_excel.read())   # ✅ COPY STREAM

            df_out = pd.read_excel(excel_copy, engine="openpyxl")
            df_out.to_csv(output_path, index=False)

        else:
            output_path = output_dir / f"Scrap_Optimization_Output_{int(heat_id)}.xlsx"

            with open(output_path, "wb") as f:
                f.write(output_excel.read())


        # -----------------------------
        # Capture LAST heat output for UI
        # -----------------------------
        # ✅ STORE LAST SUCCESSFUL OPTIMIZATION RESULT
        if output_excel is not None:
            try:
                output_excel.seek(0)
                test_df = pd.read_excel(output_excel, sheet_name="Scrap Mix")

                # check if it's a valid solution
                if "Scrap Type" in test_df.columns:
                    output_excel.seek(0)
                    last_success_excel = BytesIO(output_excel.read())
                    last_success_heat = heat_id
                    last_success_heat_row = heat_row.copy()

            except:
                pass


    # last_output_excel = first_output_excel
    if 'last_success_excel' in locals():
        last_output_excel = last_success_excel
    else:
        return [], [], None, None
    # Try reading as Excel first
    last_output_excel.seek(0)

    df_scrap = pd.read_excel(last_output_excel, sheet_name="Scrap Mix", engine="openpyxl")

    # ✅ HANDLE NO SOLUTION CASE
    if "Scrap Type" not in df_scrap.columns:
        return [], [], None, None

    print([repr(col) for col in df_scrap.columns])

    # -----------------------------
    # 🔥 STANDARDIZE COLUMN NAMES
    # -----------------------------
    df_scrap.columns = df_scrap.columns.str.strip()
    print("test: ", df_scrap.columns)

    # Handle all variations safely
    rename_map = {}

    for col in df_scrap.columns:
        col_clean = col.lower().replace(" ", "").replace("(", "").replace(")", "").replace("$", "")

        if "quantityusedinpound" in col_clean:
            rename_map[col] = "Quantity Used (Tons)"
        elif "costindollarperpound" in col_clean:
            rename_map[col] = "Cost per Ton ($)"
        elif "totalcostcontributionindollar" in col_clean:
            rename_map[col] = "Total Cost Contribution ($)"

    df_scrap = df_scrap.rename(columns=rename_map)

    # -----------------------------
    # 🔥 ROUND VALUES
    # -----------------------------
    for col in ["Quantity Used (Tons)", "Cost per Ton ($)", "Total Cost Contribution ($)"]:
        if col in df_scrap.columns:
            df_scrap[col] = df_scrap[col].round(3)

    last_output_excel.seek(0)
    df_chem = pd.read_excel(last_output_excel, sheet_name="Chemistry", engine="openpyxl")

    # -----------------------------
    # 🔥 ADD ACTUAL QTY USING CONCAT
    # -----------------------------

    # Ensure column name matches UI requirement
    actual_qty_df_upd = first_actual_qty_df.rename(columns={
        "Actual Quantity Used": "Actual Quantity Used (Tons)"
    })

    # Keep only required column
    actual_qty_df_upd = actual_qty_df_upd[['Scrap Type', 'Actual Quantity Used (Tons)']]

    # Reset index to align row-wise
    df_scrap = df_scrap.reset_index(drop=True)
    actual_qty_df_upd = actual_qty_df_upd.reset_index(drop=True)

    # CONCAT (no merge as per your requirement)
    # df_scrap = pd.concat([df_scrap, actual_qty_df_upd], axis=1)
    df_scrap = pd.merge(df_scrap, actual_qty_df_upd, on="Scrap Type", how="outer")  # 🔥 IMPORTANT

    # -----------------------------
    # FIX COLUMN ORDER + CLEANUP
    # -----------------------------

    # Remove 'Unnamed: 0' if exists
    if 'Unnamed: 0' in df_chem.columns:
        df_chem = df_chem.rename(columns={'Unnamed: 0': ''})

    # Move Achieved Chemistry column to first
    if '' in df_chem.columns:
        cols = [''] + [c for c in df_chem.columns if c != '']
        df_chem = df_chem[cols]

    # Round all numeric values
    df_chem = df_chem.round(3)

    # Filter Scrap Mix
    # -----------------------------
    # SAFE COLUMN HANDLING
    # -----------------------------
    if "Quantity Used (Tons)" in df_scrap.columns:
        df_scrap = df_scrap[['Scrap Type', "Quantity Used (Tons)","Actual Quantity Used (Tons)", "Cost per Ton ($)",]]
        # df_scrap = df_scrap[df_scrap["Quantity Used (Tons)"] > 0]
        df_scrap = df_scrap[(df_scrap["Quantity Used (Tons)"] > 0) | (df_scrap["Actual Quantity Used (Tons)"] > 0)]

        # ROUND VALUES TO 3 DECIMALS
        df_scrap["Quantity Used (Tons)"] = df_scrap["Quantity Used (Tons)"].round(3)
        df_scrap["Cost per Ton ($)"] = df_scrap["Cost per Ton ($)"].round(3)
    else:
        # fallback when no solution
        df_scrap = df_scrap.copy()

    # -----------------------------
    # 🔥 COST CALCULATIONS
    # -----------------------------

    # actual_cost = (df_scrap['Actual Quantity Used'] * df_scrap['Cost per Ton ($)']).sum()
    cost_col = "Cost per Ton ($)" if "Cost per Ton ($)" in df_scrap.columns else "Cost per Ton"
    qty_col = "Quantity Used (Tons)" if "Quantity Used (Tons)" in df_scrap.columns else "Quantity Used"

    # ✅ DETECT CORRECT COST COLUMN
    cost_col = None
    if "Cost per Ton ($)" in df_scrap.columns:
        cost_col = "Cost per Ton ($)"
    elif "Cost per Ton" in df_scrap.columns:
        cost_col = "Cost per Ton"

    qty_col = "Quantity Used (Tons)" if "Quantity Used (Tons)" in df_scrap.columns else "Quantity Used"

    if df_scrap.empty or cost_col is None:
        actual_cost = None
        suggested_cost = None
    else:
        if 'Actual Quantity Used (Tons)' in df_scrap.columns:
            actual_cost = (df_scrap['Actual Quantity Used (Tons)'] * df_scrap[cost_col]).sum()
        else:
            actual_cost = None

        suggested_cost = (df_scrap[qty_col] * df_scrap[cost_col]).sum()

    actual_cost = round(actual_cost, 3) if actual_cost is not None else None
    suggested_cost = round(suggested_cost, 3) if suggested_cost is not None else None

    # ---------------------------------
    # FINAL UI COLUMN RENAME
    # ---------------------------------
    df_scrap = df_scrap.rename(columns={
        "Quantity Used (Tons)": "Suggested Quantity Used (Pounds)",
        "Actual Quantity Used (Tons)": "Actual Quantity Used (Pounds)",
        "Cost per Ton ($)": "Cost per Pound"
    })


    # Convert to JSON for UI
    scrap_json = df_scrap.to_dict(orient="records")
    # chem_json = df_chem.to_dict(orient="records")
    chem_json = json.loads(df_chem.to_json(orient="records"))

    # return True
    return scrap_json, chem_json, actual_cost, suggested_cost

