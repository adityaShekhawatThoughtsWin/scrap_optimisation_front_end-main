import pandas as pd
import numpy as np
from copy import deepcopy
from pathlib import Path

from optimizer_code import run_optimization_pulp2

import queue
import threading
import logbook


# Sentinel object — placed in subscriber queues when a log run is complete
_DONE = object()

# ── Pub/sub registry ──────────────────────────────────────────────────────────
# Each active SSE client registers a queue here. /generateLogs fans out to all.

_subscribers: list[queue.Queue] = []
_subscribers_lock = threading.Lock()


def _broadcast(item):
    """Push item to every active subscriber queue."""
    with _subscribers_lock:
        for q in _subscribers:
            q.put(item)


def _register() -> queue.Queue:
    q: queue.Queue = queue.Queue()
    with _subscribers_lock:
        _subscribers.append(q)
    return q


def _unregister(q: queue.Queue):
    with _subscribers_lock:
        _subscribers.remove(q)


# ── Custom logbook handler ────────────────────────────────────────────────────

class BroadcastHandler(logbook.Handler):
    """
    Captures logbook records and fans out formatted lines to all SSE subscribers.
    """

    FORMAT = "[{level}] {channel}: {message}"

    def __init__(self, level=logbook.DEBUG):
        super().__init__(level=level, bubble=True)

    def emit(self, record: logbook.LogRecord):
        line = self.FORMAT.format(
            level=record.level_name,
            channel=record.channel,
            message=record.message,
        )
        _broadcast(line)

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "future_heat_inputs"
OUTPUT_DIR = BASE_DIR / "outputs"
PLANNER_OUTPUT_FILENAME = "Scarp_Mix_Recommendation_File.xlsx"


def _scrap_type_col(df, label="dataframe"):
    for col in ("Scrap_Type", "Scrap Type"):
        if col in df.columns:
            return col
    raise KeyError(f"{label} must contain 'Scrap_Type' or 'Scrap Type'")


def load_kf_input_dataframe(kf_source):
    """Load KF Input sheet from path or use a pre-built DataFrame."""
    if isinstance(kf_source, pd.DataFrame):
        return kf_source.copy()
    kf_path = Path(kf_source)
    if kf_path.suffix.lower() in (".xlsx", ".xls", ".xlsm"):
        try:
            return pd.read_excel(kf_path, sheet_name="Input")
        except ValueError:
            return pd.read_excel(kf_path)
    raise ValueError(f"Unsupported KF file type: {kf_path}")


def run_planner(
    heat_query: pd.DataFrame,
    scrap_availability_df: pd.DataFrame,
    grade_spec_df: pd.DataFrame,
    kf_source,
    output_dir=None,
):
    """Run future-heats planner and save the recommendation workbook."""
    output_dir = Path(output_dir or OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    kf_input_df = load_kf_input_dataframe(kf_source)
    final_result, final_result_qty = future_heats(
        heat_query=heat_query,
        scrap_availability_df=scrap_availability_df,
        grade_spec_df=grade_spec_df,
        kf_file=kf_input_df,
    )

    handler = BroadcastHandler()

    output_file = output_dir / PLANNER_OUTPUT_FILENAME
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        final_result.to_excel(writer, sheet_name="Scrap Mix (%)", index=False)
        final_result_qty.to_excel(writer, sheet_name="Scrap Mix (Tons)", index=False)
    with handler.applicationbound():
        boot  = logbook.Logger("Boot") 
        boot.info(f"Saved planner result: {output_file}") 
    print(f"Saved planner result: {output_file}")
    return output_file, final_result


def future_heats(heat_query: pd.DataFrame,
    scrap_availability_df: pd.DataFrame,
    grade_spec_df: pd.DataFrame,
    kf_file: pd.DataFrame):

    heat_query = heat_query
    heat_query["PlanWeight"] = heat_query["PlanWeight"]

    kf_input_df = kf_file

    handler = BroadcastHandler()

    # =========================================================================
    # READ KF FILE SHEETS
    # =========================================================================
    # kf_input_df = pd.read_excel(
    #     latest_kf_file,
    #     sheet_name="Input"
    # )
    with handler.applicationbound():
        boot  = logbook.Logger("Boot")
        boot.info(kf_input_df.shape)       
        print(kf_input_df.shape)

        cols1 = [c for c in ['Maximum_Usage', 'Cost', 'Yield', 'Yielded_Cost', 'Inventory', 'Fe', 'C', 'Cu', 'Ni', 'Cr', 'Mo', 'Sn', 'Si', 'Mn',' Power_Cost ()', 'Flux+C ()'] if c in kf_input_df.columns]
        boot.warning("[WARNING: ] Filling NaN with 0 for: {}".format([c for c in cols1 if kf_input_df[c].isna().any()]))
        print("[WARNING: ] Filling NaN with 0 for:", [c for c in cols1 if kf_input_df[c].isna().any()])
        kf_input_df[cols1] = kf_input_df[cols1].fillna(0)

        cols2 = [c for c in ['Maximum_Usage', 'Cost', 'Yield', 'Yielded_Cost', 'Inventory', 'Fe', 'C', 'Cu', 'Ni', 'Cr', 'Mo', 'Sn', 'Si', 'Mn',' Power_Cost ()', 'Flux+C ()'] if c in scrap_availability_df.columns]
        boot.warning("[WARNING: ] Filling NaN with 0 for: {}".format([c for c in cols2 if scrap_availability_df[c].isna().any()]))
        print("[WARNING: ] Filling NaN with 0 for:", [c for c in cols2 if scrap_availability_df[c].isna().any()])
        scrap_availability_df[cols2] = scrap_availability_df[cols2].fillna(0)

        # -------------------------------------------------------------------------
        # Chemistry columns
        # -------------------------------------------------------------------------
        chemistry_cols = ["Cu", "Ni", "Sn", "Cr", "P"]

        # -------------------------------------------------------------------------
        # Divide chemistry by 100 in KF Input
        # -------------------------------------------------------------------------
        # for col in chemistry_cols:

        #     if col in kf_input_df.columns:
        #         kf_input_df[col] = (
        #             pd.to_numeric(
        #                 kf_input_df[col],
        #                 errors="coerce"
        #             ) / 100
        #         )

        #Read Target Sheet
        #kf_target_df = pd.read_excel(
        #   latest_kf_file,
        #  sheet_name="Target"
        #)

        #Read Parameters Sheet
        # print(kf_target_df.shape)

        #kf_parameters_df = pd.read_excel(
        #   latest_kf_file,
        #  sheet_name="Parameters"
        #)

        # print(kf_parameters_df.shape)


        # =========================================================================
        # READ Scrap Availability FILE SHEETS
        # =========================================================================

        scrap_availability_df = scrap_availability_df

        for col in ["Yielded_Cost", " Power_Cost ()", "Flux+C ()"]:
            scrap_availability_df[col] = scrap_availability_df[col].astype(str).str.replace("$", "", regex=False).str.strip().astype(float)
            scrap_availability_df[col] = scrap_availability_df[col].fillna(0.00)


        df1_input = deepcopy(scrap_availability_df)

        # -------------------------------------------------------------------------
        # Copy chemistry columns from KF input to scrap availability
        # -------------------------------------------------------------------------
        # Find scrap types not matching
        kf_scrap_col = _scrap_type_col(kf_input_df, "KF input")
        missing_scraps = (
            set(df1_input["Scrap_Type"].dropna().astype(str).str.strip())
            - set(kf_input_df[kf_scrap_col].dropna().astype(str).str.strip())
        )

        # Print unmatched scrap types
        if missing_scraps:
            boot.warning("[WARNING] We could not find the following scrap types in the KF file: {}".format(sorted(missing_scraps)))
            print("\n[WARNING] We could not find the following scrap types in the KF file:\n", sorted(missing_scraps))

        # Print chemistry columns not present in scrap availability
        missing_chem_cols = [c for c in chemistry_cols if c not in df1_input.columns]
        
        if missing_chem_cols:
            boot.warning("[WARNING] Below chemistry columns not present in Scrap Availability file so KF chemistry values could not be updated: {}".format(missing_chem_cols))
            print(
                "\n[WARNING] Below chemistry columns not present in Scrap Availability file "
                "so KF chemistry values could not be updated:\n",
                missing_chem_cols
            )

        # Update only existing chemistry columns
        for col in [c for c in chemistry_cols if c in df1_input.columns and c in kf_input_df.columns]:

            temp_map = dict(
                zip(
                    kf_input_df[kf_scrap_col].astype(str).str.strip(),
                    kf_input_df[col]
                )
            )

            df1_input[col] = (
                df1_input["Scrap_Type"]
                .astype(str)
                .str.strip()
                .map(temp_map)
                .fillna(0.00)
            )

        df1_input["Total Yield + Power+ Flux Cost"] = (df1_input["Yielded_Cost"] + df1_input[" Power_Cost ()"] + df1_input["Flux+C ()"]) #Cost in Tons

        
        # print("scrap_availability_df: ", scrap_availability_df.shape)
        # print("org scrap columns: ", scrap_availability_df.columns)
        # print("df1_input: ", df1_input.shape)
        # print("df1_input columns: ", df1_input.columns)

        # =========================================================================
        #Read Grade Spec file (%)
        # =========================================================================
        grade_specifications_df = grade_spec_df
        grade_specifications_df = grade_specifications_df.fillna(0.00)

        grade_specifications_df = (grade_specifications_df.drop_duplicates(subset=["Grade", "Spec"], keep="first"))


        # =========================================================================
        # FINAL RESULT DF
        # =========================================================================
        # final_result = pd.DataFrame()
        final_result = pd.DataFrame(columns=scrap_availability_df['Scrap_Type'].to_list())
        
        heats = heat_query['HeatID'].to_list()
        final_result.insert(0,"HeatID",heat_query['HeatID'])
        final_result.insert(1,"GradeName",heat_query['GradeName'])
        final_result.insert(2,"PlanWeight",heat_query['PlanWeight']/2000)
        final_result.insert(3,"Status",[None for i in range(len(heats))])
        final_result.insert(4,"Min Target Cu",[None for i in range(len(heats))])
        final_result.insert(5,"Max Target Cu",[None for i in range(len(heats))])
        
        ele_list = ['Fe', 'C', 'Cu', 'Ni', 'Cr', 'Mo', 'Sn', 'Si', 'Mn']
        ele_col = [ele for ele in ele_list]
        final_result[ele_col] = None

        final_result['Total Cost ($)'] = None
        final_result['Cost per Ton of Steel ($)'] = None
        # final_result['Cost per Ton of Scrap ($)'] = None

        # final_result.head()
        final_result_qty = deepcopy(final_result)
        # =========================================================================
        # TRACK DUPLICATES
        # =========================================================================
        processed_heat_ids = set()

        # =========================================================================
        # TRACK PREVIOUS HEAT CONSUMPTION
        # =========================================================================
        previous_heat_consumption = {}

        # =========================================================================
        # LOOP THROUGH HEATS
        # =========================================================================
        for idx, heat_row in heat_query.iterrows():

            # ---------------------------------------------------------------------
            # Get HeatID
            # ---------------------------------------------------------------------
            heat_id = heat_row["HeatID"]

            # ---------------------------------------------------------------------
            # Skip duplicate HeatIDs
            # ---------------------------------------------------------------------
            if heat_id in processed_heat_ids:

                boot.info(f"[INFO] HeatID {heat_id} duplicate found. Skipping.")
                print(
                    f"[INFO] HeatID {heat_id} duplicate found. "
                    f"Skipping."
                )

                continue

            # ---------------------------------------------------------------------
            # Add to processed
            # ---------------------------------------------------------------------
            processed_heat_ids.add(heat_id)
            boot.info(f"Processing HeatID -> {heat_id}") 
            print(f"\nProcessing HeatID -> {heat_id}")

            # =========================================================================
            # UPDATE TARGET SHEET
            # =========================================================================
            # Get grade name
            # df2_target = deepcopy(kf_target_df)
            
            df2_target = pd.DataFrame({"Element":ele_list,
                                    "Min":[0 for i in range(len(ele_list))],
                                    "Max":[100 for i in range(len(ele_list))]})
            
            # Default values
            df2_target["Min"], df2_target["Max"] = 0.0, 100.0

            # Restrict example
            restrict_element = ["Cu"]   # [] or None for all

            # Convert both to clean string
            grade_specifications_df["Grade"] = (
                grade_specifications_df["Grade"]
                .astype(str)
                .str.strip()
            )

            current_grade = str(heat_row["GradeName"]).strip()

            # Filter grade
            grade_filtered = grade_specifications_df[
                grade_specifications_df["Grade"] == current_grade
            ]
            if grade_filtered.empty:
                boot.warning(f"[WARNING] Grade '{current_grade}' not found in Grade Specification file. Using default values.")
                print(f"[WARNING] Grade '{current_grade}' not found in Grade Specification file. Using default values.")
            # print(grade_filtered.head())

            
            boot.info(f"filtered grade spec: {heat_row["GradeName"]}") 
            print("filtered grade spec: ", heat_row["GradeName"])

            if not grade_filtered.empty:

                min_row = grade_filtered[grade_filtered["Spec"] == "Min"].iloc[0]
                max_row = grade_filtered[grade_filtered["Spec"] == "Max"].iloc[0]

                # Elements to update
                elements = restrict_element if restrict_element else df2_target["Element"]

                for ele in elements:

                    mask = df2_target["Element"].str.strip().str.upper() == ele.upper()

                    df2_target.loc[mask, "Min"] = min_row.get(ele, 0.0)
                    df2_target.loc[mask, "Max"] = max_row.get(ele, 100.0)

                    if ele == 'Fe':
                        df2_target.loc[mask, "Min"] = min_row.get(ele, 93.0)
                        df2_target.loc[mask, "Max"] = max_row.get(ele, 100.0)

                # print(df2_target.head())

            # =========================================================================
            # UPDATE PARAMETERS SHEET
            # =========================================================================

            # Create working copy
            # df3_parameters = deepcopy(
            #    kf_parameters_df
            # )

            # Update plan weight
            plan_weight = heat_row["PlanWeight"] / 2000 # Convert pounds to tons

            # Update parameter value
            # parameter_mask = (
            #   df3_parameters["Parameter"]
            #  == "Total capacity per heat"
            #)

            # df3_parameters.loc[
            #   parameter_mask,
            #  "Value"
            # ] = plan_weight

            # print(df3_parameters.head())

            ########################################################################
            # Update inventory using previous heat optimization output
            df1_input["Inventory"] = df1_input["Inventory"] - df1_input["Scrap_Type"].map(previous_heat_consumption).fillna(0)

            # Prevent negative inventory
            df1_input["Inventory"] = df1_input["Inventory"].clip(lower=0)

            # print(df1_input.head())

            #=========================================================================
            # ******************RUN OPTIMIZATION******************
            #=========================================================================
            opt_result, chemistry_df = run_optimization_pulp2(df1_input, df2_target, plan_weight)

            boot.info(f"shape of opt result: {opt_result.shape}")
            print("shape of opt result: ", opt_result.shape)
            # opt_result = run_optimization_pulp_dummy(input_filename)
            # print(opt_result.shape)
            # print(opt_result.columns)

            # =========================================================================
            # ADD HEAT ID
            # =========================================================================
            opt_result["HeatID"] = heat_id
            chemistry_df["HeatID"] = heat_id

            #=========================================================================
            #STORE CURRENT HEAT CONSUMPTION
            #=========================================================================
            previous_heat_consumption = dict(
                zip(
                    opt_result["Scrap_Type"],
                    opt_result['Quantity Used in Tons']
                )
            )

            #=========================================================================
            # Keep rows where:
            # 1. Quantity Used in Pound > 0
            # OR
            # 2. Scrap Type contains "No Solutions Found"
            #=========================================================================
            opt_result = opt_result[
                (opt_result["Quantity Used in Tons"] > 0)
                |
                (
                    opt_result["Scrap_Type"]
                    .astype(str)
                    .str.contains("No Solution Found", case=False, na=False)
                )
            ]

            #=========================================================================
            #APPEND FINAL RESULT
            #=========================================================================
            #final_result = pd.concat(
            #  [
            #     final_result,
            #    opt_result
                #],
                #ignore_index=True
            #)
            
            # update qty values
            row_mask = final_result["HeatID"] == heat_id
            
            cols = list(previous_heat_consumption.keys())
            # qty_values = np.array(list(previous_heat_consumption.values()))
            # curr_qty_values = final_result.loc[row_mask, cols]

            # show output as prop in %
            total_scrap_used = sum(previous_heat_consumption.values())
            qty_values = [round(v,3) for v in previous_heat_consumption.values()]
            prop_values = [round(v * 100/total_scrap_used,0) for v in previous_heat_consumption.values()]
            
            # final_result.loc[row_mask, cols] = np.where(qty_values>0, qty_values, curr_qty_values)
            final_result.loc[row_mask, cols] = prop_values
            
            # update chemistry values
            final_result.set_index('HeatID', inplace=True)
            chemistry_df.set_index('HeatID', inplace=True)
            final_result.update(chemistry_df)
            final_result.reset_index(inplace=True)
            
            # Update total cost
            total_cost = opt_result['Total Cost Contribution ($)'].sum()
            total_tonnage_scrap = opt_result['Quantity Used in Tons'].sum()
            total_tonnage = opt_result['Quantity Used in Tons'].sum()
            final_result.loc[row_mask, ['Total Cost ($)']] = round(total_cost, 2)
            final_result.loc[row_mask, ['Cost per Ton of Steel ($)']] = round(total_cost/plan_weight, 2)
            # final_result.loc[row_mask, ['Cost per Ton of Scrap ($)']] = round(total_cost / total_tonnage_scrap, 2)
            
            # Update Min Max for Cu
            final_result.loc[row_mask, ['Min Target Cu']] = df2_target.loc[df2_target['Element'] == 'Cu','Min'].values[0]
            final_result.loc[row_mask, ['Max Target Cu']] = df2_target.loc[df2_target['Element'] == 'Cu','Max'].values[0]

            # Update Status
            if opt_result["Scrap_Type"].astype(str).str.contains("No Solution Found", case=False, na=False).sum():
                final_result.loc[row_mask, ['Status']] = 'No Solution Found'
            else:
                final_result.loc[row_mask, ['Status']] = 'Scheduled'

            if 'No Solution Found' in final_result.columns:
                final_result = final_result.drop(columns=['No Solution Found'])

            # Update qty df
            final_result_qty.loc[row_mask, final_result_qty.columns] = final_result.loc[row_mask]
            final_result_qty.loc[row_mask, cols] = qty_values

            # print("dict: ", previous_heat_consumption)
        _broadcast(_DONE)

    return final_result, final_result_qty


if __name__ == "__main__":
    heat_query = pd.read_csv(INPUT_DIR / "HeatQuery.CSV")
    scrap_availability_df = pd.read_excel(INPUT_DIR / "Scrap_Data_Daily_Inventory.xlsx")
    grade_spec_df = pd.read_excel(INPUT_DIR / "Grade_Specifications.xlsx")
    kf_file = INPUT_DIR / "KF_Scrap_Type_Predictions_27495.xlsx"

    run_planner(
        heat_query=heat_query,
        scrap_availability_df=scrap_availability_df,
        grade_spec_df=grade_spec_df,
        kf_source=kf_file,
        output_dir=OUTPUT_DIR,
    )

