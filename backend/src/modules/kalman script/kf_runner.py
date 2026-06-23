from pathlib import Path
import sys
import traceback

from Kalman_Scrap_Chemistry_Prediction import KalmanFilterScrapChemistry, ScrapKalmanConfig

ALL_CHEMS = ["Cu", "Ni", "Sn", "Cr", "P"]
MODEL_NAMES = ["LinearRegression_ScrapModel_Cu.pkl"]


def get_runtime_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_bundle_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def resolve_uploads_dir() -> Path:
    runtime_dir = get_runtime_path()
    for name in ("Uploads", "uploads"):
        candidate = runtime_dir / name
        if candidate.exists():
            return candidate
    fallback = runtime_dir / "Uploads"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def resolve_config_file(filename: str) -> Path:
    runtime_dir = get_runtime_path()
    bundle_dir = get_bundle_path()
    for base in (runtime_dir, bundle_dir):
        for folder in ("Uploads", "uploads"):
            candidate = base / folder / filename
            if candidate.exists():
                return candidate
    return resolve_uploads_dir() / filename


def run_kf_pipeline(
    input_file,
    output_dir,
    target_chem,
    numb_heats_pass,
    chemistry_file_path=None,
    input_ext=None,
    csv_encoding=None,
):
    """
    Run Kalman filter for one target chemistry.
    Returns (success, message, output_file_path).
    """
    try:
        cfg = ScrapKalmanConfig(
            input_data_path=Path(input_file),
            scrap_limits_path=resolve_config_file("Scrap_Cost_Chemistry_Limits.xlsx"),
            model_folder=get_bundle_path() / "Saved_Models",
            model_names=MODEL_NAMES,
            selected_model_name=MODEL_NAMES[0],
            target_chem=target_chem,
            numb_heats_pass=int(numb_heats_pass),
            output_dir=Path(output_dir),
            apply_scaling_mode="manual",
            scaler_type="standard",
            use_previous_kf=False,
            csv_encoding=csv_encoding,
        )

        cfg.chemistry_file_path = chemistry_file_path
        cfg.input_ext = input_ext
        cfg.feature_variables_path = resolve_config_file("Scrap_Chem_Input_Variables.xlsx")
        cfg.template_path = resolve_config_file("Recom_Scrap_Input_3 1.xlsx")

        runner = KalmanFilterScrapChemistry(cfg)
        output_file = runner.run()

        if output_file is None:
            return False, f"Kalman completed for {target_chem} but no output file was produced", None

        return True, f"Kalman Filter Prediction Successfully Completed for {target_chem}", Path(output_file)

    except Exception as e:
        return False, str(e) + "\n" + traceback.format_exc(), None


def run_kf_configuration(
    input_file,
    chemistry_file_path,
    output_dir,
    target_chem_ui,
    numb_heats_pass,
    input_ext=None,
    csv_encoding=None,
):
    """
    Mirror KF_configuration.py: run one or all chems, return final output workbook path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chem_list = ALL_CHEMS if target_chem_ui == "ALL" else [target_chem_ui]
    results = []
    final_output_file = None

    for chem in chem_list:
        print(f"Running KF for target chem: {chem} (numb_heats_pass={numb_heats_pass})")
        success, message, output_file = run_kf_pipeline(
            input_file=input_file,
            output_dir=output_dir,
            target_chem=chem,
            numb_heats_pass=numb_heats_pass,
            chemistry_file_path=chemistry_file_path,
            input_ext=input_ext,
            csv_encoding=csv_encoding,
        )
        results.append((chem, success, message))
        if output_file is not None:
            final_output_file = output_file

    all_success = all(r[1] for r in results)
    combined_message = "\n".join(f"{chem}: {msg}" for chem, _, msg in results)

    return all_success, combined_message, final_output_file
