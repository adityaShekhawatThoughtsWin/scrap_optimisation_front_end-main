import pandas as pd
from Kalman_Scrap_Chemistry_Prediction import *


# ==========================================
# INPUTS
# ==========================================

target_chem = "ALL"

numb_heats_pass = 50

input_file = BASE_DIR / "Uploads" / "HeatQuery_All_03312026063851_cap.CSV"

chemistry_file_path = BASE_DIR / "Uploads" / "HeatQuery_Chemistry_03312026063850_cap.CSV"

scrap_limits_path = BASE_DIR / "Uploads" / "Scrap_Cost_Chemistry_Limits.xlsx"

feature_variables_path = BASE_DIR / "Uploads" / "Scrap_Chem_Input_Variables.xlsx"

template_path = BASE_DIR / "Uploads" / "Recom_Scrap_Input_3 1.xlsx"

model_folder = BASE_DIR / "Saved_Models"

OUTPUT_FOLDER = BASE_DIR / "outputs"

# ==========================================

if target_chem == "ALL":

    all_chems = ['Cu', 'Ni', 'Sn', 'Cr', 'P']

    for chem in all_chems:

        print(f"\nRunning KF for: {chem}")

        # Keep SAME model for all
        model_names = ["LinearRegression_ScrapModel_Cu.pkl"]

        cfg = ScrapKalmanConfig(
            input_data_path=Path(input_file),
            scrap_limits_path=Path(scrap_limits_path),
            model_folder=Path(model_folder),
            model_names=model_names,
            selected_model_name=model_names[0],
            target_chem=chem,
            numb_heats_pass=numb_heats_pass,
            output_dir=Path(OUTPUT_FOLDER),
            apply_scaling_mode="manual",
            scaler_type="standard",
            use_previous_kf=False,
        )

        cfg.chemistry_file_path = chemistry_file_path
        cfg.feature_variables_path = feature_variables_path
        cfg.template_path = template_path

        runner = KalmanFilterScrapChemistry(cfg)

        runner.run()

        print(f"{chem} completed successfully")


else:

    model_names = ["LinearRegression_ScrapModel_Cu.pkl"]

    cfg = ScrapKalmanConfig(
        input_data_path=Path(input_file),
        scrap_limits_path=Path(scrap_limits_path),
        model_folder=Path(model_folder),
        model_names=model_names,
        selected_model_name=model_names[0],
        target_chem=target_chem,
        numb_heats_pass=numb_heats_pass,
        output_dir=Path(OUTPUT_FOLDER),
        apply_scaling_mode="manual",
        scaler_type="standard",
        use_previous_kf=False,
    )

    cfg.chemistry_file_path = chemistry_file_path
    cfg.feature_variables_path = feature_variables_path
    cfg.template_path = template_path

    runner = KalmanFilterScrapChemistry(cfg)

    output_file = runner.run()
    # runner.run()

    print(f"{target_chem} completed successfully")
    print("Final Output File:", output_file) #For UI you can directly use return send_file(output_file) or return jsonify({"output_file": output_file})

