import platform
import shutil
import sys
from pathlib import Path

import pandas as pd
from pulp import COIN_CMD, PULP_CBC_CMD


def get_cbc_solver(msg=False, base_dir=None):
    """Return a PuLP CBC solver for the current platform."""
    if getattr(sys, "frozen", False):
        base_dir = Path(sys._MEIPASS)
    elif base_dir is None:
        base_dir = Path(__file__).parent
    else:
        base_dir = Path(base_dir)

    solver_name = "cbc.exe" if platform.system() == "Windows" else "cbc"
    bundled = base_dir / "solver" / solver_name
    if bundled.exists():
        print("🔍 Using bundled CBC solver at:", bundled)
        return COIN_CMD(path=str(bundled), msg=msg)

    system_cbc = shutil.which("cbc")
    if system_cbc:
        print("🔍 Using system CBC solver at:", system_cbc)
        return COIN_CMD(path=system_cbc, msg=msg)

    print("🔍 Using PuLP default CBC solver")
    return PULP_CBC_CMD(msg=msg)

def clean_grade_spec_excel(file_path, sheet_name=0):

    df = pd.read_excel(file_path)

    # Clean Grade column
    df["Grade"] = (
        df["Grade"]
        .astype(str)
        .str.replace(r"\*", "", regex=True)
        .str.replace(r"\(Mingo\)", "", regex=True)
        .str.strip()
    )

    # Fill nulls
    df = df.fillna(0)
    df = df.replace(r"^\s*$", 0, regex=True)

    return df


def enforce_grade_spec_limits(heat_id, original_data_reference, result_df, target_df):
    
    # ---------------------------------------------------------
    # Get GradeName for current heat_id
    # ---------------------------------------------------------
    grade_name = (
        original_data_reference.loc[
            original_data_reference["HeatID"] == heat_id,
            "GradeName"
        ]
        .iloc[0]
    )

    # Clean GradeName
    grade_name = (
        str(grade_name)
        .replace("*", "")
        .replace("(Mingo)", "")
        .strip()
    )

    print(grade_name)

    # ---------------------------------------------------------
    # Filter grade spec for this grade
    # ---------------------------------------------------------
    grade_spec = result_df[
        result_df["Grade"] == grade_name
    ]

    if grade_spec.empty:
        return target_df
    # else:
    #     print(grade_spec)

    # ---------------------------------------------------------
    # Get Min/Max rows
    # ---------------------------------------------------------
    min_row = grade_spec[
        grade_spec["Spec"].astype(str).str.upper() == "MIN"
    ]

    max_row = grade_spec[
        grade_spec["Spec"].astype(str).str.upper() == "MAX"
    ]

    if min_row.empty or max_row.empty:
        return target_df

    min_row = min_row.iloc[0]
    max_row = max_row.iloc[0]

    # ---------------------------------------------------------
    # Apply chemistry limit checks
    # ---------------------------------------------------------
    for idx, row in target_df.iterrows():

        Element = row["Element"]

        # skip if element not present in grade spec
        if Element not in grade_spec.columns:
            continue

        grade_spec_min = pd.to_numeric(min_row.get(Element, 0), errors="coerce")
        grade_spec_max = pd.to_numeric(max_row.get(Element, 0), errors="coerce")

        grade_spec_min = grade_spec_min / 100
        grade_spec_max = grade_spec_max / 100

        # print("Grade min: ", grade_spec_min)
        # print("Grade max: ", grade_spec_max)

        # updated_min = pd.to_numeric(row["Min"], errors="coerce")
        # updated_max = pd.to_numeric(row["Max"], errors="coerce")

        updated_min = row["Min"]
        updated_max = row["Max"]

        updated_min = updated_min / 100
        updated_max = updated_max / 100

        # print("Updated min: ", updated_min)
        # print("Updated max: ", updated_max)

        # -----------------------------------------------------
        # MAX LOGIC
        # -----------------------------------------------------
        if pd.notna(grade_spec_max):

            if updated_max > grade_spec_max:
                target_df.at[idx, "Max"] = grade_spec_max

        # -----------------------------------------------------
        # MIN LOGIC
        # -----------------------------------------------------
        if pd.notna(grade_spec_min):

            # Always use grade spec minimum
            target_df.at[idx, "Min"] = grade_spec_min

            # # apply only if grade spec min > 0
            # if grade_spec_min > 0:

            #     target_df.at[idx, "Min"] = grade_spec_min

    # ---------------------------------------------------------
    # Final rounding
    # ---------------------------------------------------------
    for col in ["Min", "Max"]:

        if col in target_df.columns:
            target_df[col] = pd.to_numeric(target_df[col], errors="coerce").round(5)
    
    # print(target_df)
    return target_df