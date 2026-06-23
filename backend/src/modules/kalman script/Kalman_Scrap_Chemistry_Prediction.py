# %%
import json
import os
import pickle
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from xml.sax import handler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import logbook

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler
from Future_Heats_Run import _DONE, BroadcastHandler, _broadcast

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

BASE_DIR = get_base_path()

# %%
@dataclass
class ScrapKalmanConfig:
    input_data_path: Path
    scrap_limits_path: Path
    model_folder: Path
    model_names: List[str]
    target_chem: str = "Cu" #Default to "Cu", can be set to "Sn" or other chemicals as needed
    numb_heats_pass: int = 50
    selected_model_name: Optional[str] = None
    output_dir: Path = Path("./outputs")
    apply_scaling_mode: str = "manual"  #manual / ml / none
    scaler_type: str = "standard"
    use_previous_kf: bool = False  #NEW: whether to use last saved KF coefficients as X0 for the next run
    # None: try utf-8-sig, utf-8, cp1252, latin-1. Set e.g. "cp1252" for Excel CSV on Windows.
    csv_encoding: Optional[str] = None

    chem_min: str = field(init=False)
    chem_max: str = field(init=False)

    def __post_init__(self):
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chem_min = f"{self.target_chem}_min"
        self.chem_max = f"{self.target_chem}_max"
        if self.selected_model_name is None:
            if len(self.model_names) == 0:
                raise ValueError("model_names must contain at least one model")
            self.selected_model_name = self.model_names[0]

# %%
# ---------------------------
#helper functions
# ---------------------------
def load_models(folder_path: Path, model_names: List[str]) -> Dict[str, object]:
    available = [f for f in os.listdir(folder_path) if f.endswith(".pkl")]
    models = {}
    for fname in model_names:
        if fname not in available:
            raise FileNotFoundError(f"Model not found: {fname}")
        with open(folder_path / fname, "rb") as f:
            models[fname] = pickle.load(f)
    return models


def read_csv_auto(path: Path, preferred_encoding: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """Read CSV with explicit encoding, or try common encodings (BOM / Excel export)."""
    path = Path(path)
    if preferred_encoding:
        return pd.read_csv(path, encoding=preferred_encoding, **kwargs)
    tried = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    last_err: Optional[UnicodeDecodeError] = None
    for enc in tried:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError as e:
            last_err = e
    raise ValueError(
        f"Could not decode {path}; tried encodings: {', '.join(tried)}. "
        "Re-save as UTF-8 or set ScrapKalmanConfig.csv_encoding (e.g. 'cp1252')."
    ) from last_err


# %%
def read_scrap_limits(scrap_limits_path: Path, target_chem: str):
    df = pd.read_excel(scrap_limits_path)
    df = df.rename(columns=lambda c: c.replace("%", "").strip())
    chem_min = f"{target_chem}_min"
    chem_max = f"{target_chem}_max"
    required_cols = ["Scrap Category", "Scrap Type", "Scrap Type Ref", chem_min, chem_max]
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"Scrap limits missing column: {c}")
    df = df[required_cols].copy()
    df[chem_min] = df[chem_min].astype(float) * 100
    df[chem_max] = df[chem_max].astype(float) * 100
    return df

# %%
def derive_chemistry_scrap_mix(
    scrap_df: pd.DataFrame,
    scrap_cols: List[str],
    target_chem: str,
) -> pd.DataFrame:
    df = scrap_df.copy()
    
    df["ProdDate"] = pd.to_datetime(df.get("ProdDate"), errors="coerce")
    df["FirstSequenceHeatID"] = df.get("FirstSequenceHeatID", "").astype(str).fillna("")
    df["LastSequenceHeatID"] = df.get("LastSequenceHeatID", "").astype(str).fillna("")
    df["SequenceID"] = df["FirstSequenceHeatID"].astype(str) + "_" + df["LastSequenceHeatID"].astype(str)
    df = df.sort_values(["SequenceID", "ProdDate"]).reset_index(drop=True)

    # --- NEW: drop rows with missing TapWeightActual to avoid NaNs downstream ---
    if "TapWeightActual" not in df.columns:
        raise ValueError("Input missing required column: 'TapWeightActual'")
    missing_mask = df["TapWeightActual"].isna()
    if missing_mask.any():
        removed = df.loc[missing_mask, "HeatID"].tolist() if "HeatID" in df.columns else df.index[missing_mask].tolist()
        print(f"Dropping {missing_mask.sum()} rows with missing TapWeightActual. Removed HeatIDs/indices: {removed}")
        df = df.loc[~missing_mask].reset_index(drop=True)
    # -------------------------------------------------------------------------

    df["TapWeightActual_Ton"] = df["TapWeightActual"] / 1000.0
    df["Total_input_scrapweight"] = df[scrap_cols].sum(axis=1) / 1000.0
    base = df["Total_input_scrapweight"] - df["TapWeightActual_Ton"] - df["LossTons"]
    grp = df["FirstSequenceHeatID"].ne(df["FirstSequenceHeatID"].shift()).cumsum()
    df["PrevHotHeel"] = base.groupby(grp).cumsum()
    df.loc[df["FirstSequenceHeatID"].ne(df["FirstSequenceHeatID"].shift()), "PrevHotHeel"] = 0
    df["Comp_from_scrap"] = (
        (df["PrevHotHeel"] + df["Total_input_scrapweight"]) * df[target_chem]
        - df["PrevHotHeel"] * df[target_chem].shift()
    ) / df["Total_input_scrapweight"]
    df["Comp_from_scrap"] = df["Comp_from_scrap"].round(6)
    df.loc[df.index[0], "Comp_from_scrap"] = df.loc[df.index[0], target_chem]
    df["Error"] = (df[target_chem] - df["Comp_from_scrap"]) / df["Comp_from_scrap"] * 100
    lab_col = f"{target_chem}_lab"
    df = df.rename(columns={target_chem: lab_col, "Comp_from_scrap": target_chem})
    return df

# %%
def scale_planning_data(
    df: pd.DataFrame,
    scrap_cols: List[str],
    mode: str = "manual",
    scaler_type: str = "standard",
):
    out = df.copy()
    if mode == "none":
        return out, None
    if mode == "ml":
        scaler_cls = {"standard": StandardScaler, "minmax": MinMaxScaler, "robust": RobustScaler}.get(scaler_type)
        if scaler_cls is None:
            raise ValueError("scaler_type must be one of standard/minmax/robust")
        scaler = scaler_cls()
        out[scrap_cols] = scaler.fit_transform(out[scrap_cols])
        return out, scaler
    if mode == "manual":
        total = out[scrap_cols].sum(axis=1).replace(0, np.nan)
        out[scrap_cols] = out[scrap_cols].div(total, axis=0)
        return out, None
    raise ValueError("mode must be one of none/ml/manual")

# %%
def kalman_scrap_chemistry_update_bounded(
    x_prev,
    P_prev,
    Q,
    R,
    W_scrap_frac,
    C_meas,
    lb,
    ub
):
    """
    Bounded Kalman filter update for scrap chemistry.
    Parameters
    ----------
    x_prev : array-like, shape (n,)
        Previous state estimate
    P_prev : array-like, shape (n,n)
        Previous covariance
    Q : array-like, shape (n,n)
        Process noise covariance
    R : array-like, shape (1,1)
        Measurement noise covariance
    W_scrap_frac : array-like, shape (1,n)
        Measurement coefficients for each scrap
    C_meas : float
        Measured value
    scrap_cols : list
        Columns corresponding to scraps (not used in this function)
    lb : array-like, shape (n,)
        Lower bounds for x
    ub : array-like, shape (n,)
        Upper bounds for x
    Returns
    -------
    Same as original function, but x_updated_flat is bounded.
    """
    import numpy as np
    from scipy.optimize import lsq_linear
 
    # ------------------------------
    # Ensure numeric format
    # ------------------------------
    x_prev = np.asarray(x_prev, dtype=float).reshape(-1, 1)
    P_prev = np.asarray(P_prev, dtype=float)
    Q = np.asarray(Q, dtype=float)
    R = np.asarray(R, dtype=float)
    W_scrap_frac = np.asarray(W_scrap_frac, dtype=float).reshape(1, -1)
    C_meas = float(C_meas)
    lb = np.asarray(lb, dtype=float)
    ub = np.asarray(ub, dtype=float)

    # ------------------------------
    # Input safety check
    # ------------------------------
    if np.isnan(W_scrap_frac).any() or np.isnan(C_meas):
        raise ValueError("NaN detected in inputs")
 
    # ------------------------------
    # PRIOR
    # ------------------------------
    x_prior = x_prev
    P_prior = P_prev + Q

 
    # ------------------------------
    # Measurement matrix
    # ------------------------------
    H = W_scrap_frac
 
    # ------------------------------
    # Prediction before update
    # ------------------------------
    k_predicted_prior = float((H @ x_prior)[0, 0])
 
    # ------------------------------
    # Innovation
    # ------------------------------
    innovation = C_meas - k_predicted_prior

    if innovation > 0:
        innovation_uncertainty = "underestimated"
    elif innovation < 0:
        innovation_uncertainty = "overestimated"
    else:
        innovation_uncertainty = "exact"
 
    # ------------------------------
    # Innovation covariance
    # ------------------------------
    S = float((H @ P_prior @ H.T)[0, 0] + R[0, 0]) + 1e-12
 
    # ------------------------------
    # Kalman gain (NO matrix inverse)
    # ------------------------------
    K = (P_prior @ H.T) / S
    kalman_gain_list = K.flatten()
 
    # ------------------------------
    # Bounded update using constrained least squares
    # ------------------------------
    # Augment system to include prior (like Kalman) + measurement
    # Weight prior by Cholesky of P_prior
    W = np.linalg.cholesky(P_prior)
    X_aug = np.vstack([W, H])
    b_aug = np.concatenate([W @ x_prior.flatten(), [C_meas]])
    # Solve bounded least squares
    result = lsq_linear(X_aug, b_aug, bounds=(lb, ub))
    x_updated_flat = result.x
    x_updated = x_updated_flat.reshape(-1, 1)
 
    # ------------------------------
    # Update covariance (simplified)
    # ------------------------------
    P_updated = (np.eye(len(x_prev)) - K @ H) @ P_prior
 
    # ------------------------------
    # Prediction AFTER update
    # ------------------------------
    k_predicted = float((H @ x_updated)[0, 0])
 
    # ------------------------------
    # Error rate
    # ------------------------------
    Error_rate = C_meas - k_predicted
 
    # ------------------------------
    # Adaptive R update
    # ------------------------------
    R_base = R[0, 0]
    # R_new = 0.9 * R_base + 0.1 * (Error_rate**2)
    # R_new = max(0.9 * R_base + 0.1 * (Error_rate**2), 1e-4)
    #Automating
    # Normalize error by current R for scale-invariance
    innov_norm_for_R = abs(innovation) / max(1e-6, R_base) #Used innovation instead of Error_rate for more responsive R adjustment based on measurement discrepancy
    # Dynamic smoothing weight: lower when error is small (faster update), higher when large (slower)
    base_weight = 0.9  # Base smoothing factor
    smoothing_weight = base_weight / (1 + innov_norm_for_R)  # Ranges ~0.45 (high error) to 0.9 (low error)
    smoothing_weight = max(0.5, min(0.95, smoothing_weight))  # Clamp to [0.5, 0.95] for stability
    adaptive_weight = 1 - smoothing_weight
    R_new = max(smoothing_weight * R_base + adaptive_weight * np.sqrt(abs(innovation**2)), 1e-4)
    R = np.array([[R_new]])
 
    # ------------------------------
    # Adaptive Q update
    # ------------------------------
    Q_base = np.mean(np.diag(Q))
    # Q_new = 0.9 * Q_base + 0.1 * (innovation**2)
    # Q_new = max(0.9 * Q_base + 0.1 * (innovation**2), 1e-6)
    #Automating
    # Normalize innovation by current Q
    innov_norm = abs(innovation) / max(1e-6, Q_base)
    # Dynamic smoothing weight: similar logic
    smoothing_weight_q = base_weight / (1 + innov_norm)
    smoothing_weight_q = max(0.5, min(0.95, smoothing_weight_q))  # Clamp
    adaptive_weight_q = 1 - smoothing_weight_q
    Q_new = max(smoothing_weight_q * Q_base + adaptive_weight_q * np.sqrt(abs(innovation**2)), 1e-6)

    Q = np.eye(len(x_prev)) * Q_new
 
    return (
        x_updated_flat,
        P_updated,
        Q,
        R,
        innovation,
        innovation_uncertainty,
        kalman_gain_list,
        k_predicted,
        Error_rate, 
        k_predicted_prior #Return prior prediction for analysis purpose (To be Removed Later)
    )

# %%
# def evaluate_kalman_metrics(self, df: pd.DataFrame, pct_threshold: float = 5.0, abs_threshold: float = 0.02):
#     y_true = df["C_meas_used"].astype(float).values
#     y_pred = df[f"{self.cfg.target_chem}_predicted"].astype(float).values
#     mask = (~np.isnan(y_true)) & (~np.isnan(y_pred)) & (~np.isinf(y_true)) & (~np.isinf(y_pred))
#     y_true = y_true[mask]
#     y_pred = y_pred[mask]
#     if len(y_true) == 0:
#         return pd.DataFrame(
#             {"Metric": ["MAE", "RMSE", "R2", "MAPE_%", "Accuracy_%"], "Value": [np.nan] * 5}
#         )

#     errors = y_true - y_pred
#     abs_errors = np.abs(errors)
#     mae = np.mean(abs_errors)
#     rmse = np.sqrt(np.mean(errors**2))
#     ss_res = np.sum(errors**2)
#     ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
#     r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0
#     non_zero_mask = y_true != 0
#     mape = np.nan
#     if np.any(non_zero_mask):
#         mape = np.mean(abs_errors[non_zero_mask] / np.abs(y_true[non_zero_mask])) * 100
#     accuracy = 100 - mape if not np.isnan(mape) else np.nan
#     pct_errors = (abs_errors / (np.abs(y_true) + 1e-12)) * 100
#     accuracy_pct_threshold = np.mean(pct_errors <= pct_threshold) * 100
#     accuracy_abs_threshold = np.mean(abs_errors <= abs_threshold) * 100

#     return pd.DataFrame(
#         {
#             "Metric": ["MAE", "RMSE", "R2", "MAPE_%", "Accuracy_%", f"Accuracy_±{pct_threshold}%", f"Accuracy_≤{abs_threshold}"],
#             "Value": [mae, rmse, r2, mape, accuracy, accuracy_pct_threshold, accuracy_abs_threshold],
#         }
#     )

# %%
def save_metrics_json(metrics_df: pd.DataFrame, output_path: Path, target_chem: str):
    payload = {
        "generated_at": datetime.now().isoformat(),
        "target_chem": target_chem,
        "metrics": metrics_df.to_dict(orient="records"),
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

# %%
class KalmanFilterScrapChemistry:
    def __init__(self, cfg: ScrapKalmanConfig):
        self.cfg = cfg
        self.models = {}
        self.selected_model = None
        self.X_test_seq = pd.DataFrame()
        self.scrap_cols = []
        self.coef_df = pd.DataFrame()
        self.kalman_df_bound = pd.DataFrame()
        self.kf_coef_df = pd.DataFrame()
        self.kf_prediction_df = pd.DataFrame()
        self.state_x = None
        self.state_P = None
        self.state_Q = None
        self.state_R = None
        self.lb = None
        self.ub = None


    def prepare(self):
        self.models = load_models(self.cfg.model_folder, self.cfg.model_names)
        if self.cfg.selected_model_name not in self.models:
            raise ValueError(f"Selected model {self.cfg.selected_model_name} not loaded")
        self.selected_model = self.models[self.cfg.selected_model_name]

        # read main input file
        # self.X_test_seq = pd.read_excel(self.cfg.input_data_path)

        handler = BroadcastHandler()

        # -----------------------------
        # Read input file (xlsx or csv). Prefer actual file extension over input_ext
        # so a .xlsx path is never read with read_csv by mistake.
        # -----------------------------
        input_path = Path(self.cfg.input_data_path)
        suf = input_path.suffix.lower()
        with handler.applicationbound():
            boot  = logbook.Logger("Boot")
            boot.info(f"Detected suffix: {suf}") 
            print(f"Detected suffix: {suf}")
            if suf == ".csv":
                boot.info("READING AS CSV")
                print("READING AS CSV")
                enc = getattr(self.cfg, "csv_encoding", None)
                self.X_test_seq = read_csv_auto(input_path, preferred_encoding=enc)
            elif suf in (".xlsx", ".xls", ".xlsm", ".xlss"):
                boot.info("READING AS EXCEL")
                print("READING AS EXCEL")
                self.X_test_seq = pd.read_excel(input_path)
            elif getattr(self.cfg, "input_ext", ".xlsx").lower() == ".csv":
                boot.info("READING AS CSV (fallback branch)")
                print("READING AS CSV (fallback branch)")
                enc = getattr(self.cfg, "csv_encoding", None)
                self.X_test_seq = read_csv_auto(input_path, preferred_encoding=enc)
            else:
                self.X_test_seq = pd.read_excel(input_path)

            chem_file_path = getattr(self.cfg, "chemistry_file_path", None)

            # -----------------------------
            # MERGE CHEMISTRY FILE LOGIC
            # -----------------------------
            if chem_file_path:

                boot.info(f"Reading Chemistry file: {chem_file_path}")
                print("📥 Reading Chemistry file:", chem_file_path)

                df_all = self.X_test_seq.copy()
                # df_chem = pd.read_excel(chem_file_path)

                # -----------------------------
                # Read chemistry file (xlsx or csv)
                # -----------------------------
                chem_p = Path(chem_file_path)
                if chem_p.suffix.lower() == ".csv":
                    enc = getattr(self.cfg, "csv_encoding", None)
                    df_chem = read_csv_auto(chem_p, preferred_encoding=enc)
                else:
                    df_chem = pd.read_excel(chem_p)

                target_chem = self.cfg.target_chem

                # Required columns
                required_cols = ["HeatName", "Chem", "AppliedTime", target_chem]
                missing_cols = [c for c in required_cols if c not in df_chem.columns]

                if missing_cols:
                    raise ValueError(f"Missing columns in Chemistry file: {missing_cols}")

                df_chem = df_chem[required_cols].copy()

                # Filter Chem = LMF
                df_chem = df_chem[df_chem["Chem"].str.lower() == "lmf"]

                # Convert datetime
                df_chem["AppliedTime"] = pd.to_datetime(df_chem["AppliedTime"], errors="coerce")

                # Sort and pick earliest per HeatName
                df_chem = df_chem.sort_values("AppliedTime")
                df_chem = df_chem.drop_duplicates(subset=["HeatName"], keep="first")

                boot.info(f"After LMF filter: {df_chem.shape}")
                print("After LMF filter:", df_chem.shape)

                # Merge
                df_merged = df_all.merge(
                    df_chem[["HeatName", target_chem]],
                    how="left",
                    left_on="HeatNumber",
                    right_on="HeatName"
                )

                # Replace target chem
                df_merged[target_chem] = df_merged[target_chem + "_y"].fillna(0)

                # Cleanup
                df_merged.drop(columns=[c for c in df_merged.columns if c.endswith("_y")], inplace=True, errors="ignore")
                df_merged.drop(columns=[c for c in df_merged.columns if c.endswith("_x")], inplace=True, errors="ignore")
                df_merged.drop(columns=["HeatName"], inplace=True, errors="ignore")

                boot.info(f"Merge completed: {df_merged.shape}")
                print("✅ Merge completed:", df_merged.shape)

                self.X_test_seq = df_merged

            # ---------- NEW: read feature list and filter input ----------
            # vars_file = self.cfg.input_data_path.parent / "Scrap_Chem_Input_Variables.xlsx"
            # vars_file = Path(r"C:\Users\OLW057\Downloads\JSW_project\ScrapOptimisation\kf_flask_app\Uploads\Scrap_Chem_Input_Variables.xlsx") #Commented on 9th April 2026
            # vars_file = BASE_DIR / "uploads" / "Scrap_Chem_Input_Variables.xlsx"
            if getattr(sys, 'frozen', False):
                runtime_dir = Path(sys.executable).parent
                bundle_dir = Path(sys._MEIPASS)
            else:
                runtime_dir = Path(__file__).parent
                bundle_dir = Path(__file__).parent

            cfg_vars = getattr(self.cfg, "feature_variables_path", None)
            if cfg_vars is not None and Path(cfg_vars).exists():
                vars_file = Path(cfg_vars)
            else:
                vars_file = None
                for base in (runtime_dir, bundle_dir):
                    for folder in ("Uploads", "uploads"):
                        candidate = base / folder / "Scrap_Chem_Input_Variables.xlsx"
                        if candidate.exists():
                            vars_file = candidate
                            break
                    if vars_file is not None:
                        break
            if vars_file is None or not vars_file.exists():
                raise FileNotFoundError(
                    f"Required feature list not found. Set cfg.feature_variables_path or place "
                    f"Scrap_Chem_Input_Variables.xlsx under Uploads/"
                )
            vars_df = pd.read_excel(vars_file)
            if "Feature_Variables" not in vars_df.columns:
                raise ValueError("Scrap_Chem_Input_Variables.xlsx must contain a column named 'Feature_Variables'")
            features = vars_df["Feature_Variables"].dropna().astype(str).str.strip().tolist()
            # ensure all listed features exist in the input data
            missing = [f for f in features if f not in self.X_test_seq.columns]
            if missing:
                boot.warning(f"Missing columns in input data as per Scrap_Chem_Input_Variables.xlsx: {missing}")
                print (f"Missing columns in input data as per Scrap_Chem_Input_Variables.xlsx: {missing}")

            features = [f for f in features if f in self.X_test_seq.columns]

            # filter input dataframe to only the requested feature columns
            self.X_test_seq = self.X_test_seq[features].copy()
            # -------------------------------------------------------------

            self.scrap_cols = [c for c in self.X_test_seq.columns if c.startswith("CHG-")]
            chg_cols_no_data = []
            for c in self.scrap_cols:
                s = self.X_test_seq[c]
                # consider empty strings as empty as well as NaN
                non_empty_mask = s.notna() & (s.astype(str).str.strip() != "")
                if not non_empty_mask.any():
                    chg_cols_no_data.append(c)
            # store list on the instance
            self.chg_cols_no_data = chg_cols_no_data

            if len(self.scrap_cols) == 0:
                raise ValueError("No scrap columns found with prefix CHG-")
            self.scrap_limits_df = read_scrap_limits(self.cfg.scrap_limits_path, self.cfg.target_chem)


    def preprocess(self):
        self.X_test_seq[self.scrap_cols] = self.X_test_seq[self.scrap_cols].fillna(0)

        # Ensure date and sequence id types before sorting
        self.X_test_seq["ProdDate"] = pd.to_datetime(self.X_test_seq["ProdDate"], errors="coerce")
        self.X_test_seq["FirstSequenceHeatID"] = self.X_test_seq["FirstSequenceHeatID"].astype(str).fillna("")
        self.X_test_seq["LastSequenceHeatID"] = self.X_test_seq["LastSequenceHeatID"].astype(str).fillna("")
        
        self.X_test_seq["SequenceID"] = (
            self.X_test_seq["FirstSequenceHeatID"].astype(str)
            + "_"
            + self.X_test_seq["LastSequenceHeatID"].astype(str)
        )
        self.X_test_seq = self.X_test_seq.sort_values(["SequenceID", "ProdDate"]).reset_index(drop=True)
        self.X_test_seq = self.X_test_seq.head(self.cfg.numb_heats_pass).copy()
        handler = BroadcastHandler()
        with handler.applicationbound():
            boot  = logbook.Logger("Boot")
            boot.info(f"Sorted by SequenceID/ProdDate and selected top {len(self.X_test_seq)} rows")
        print(f"Sorted by SequenceID/ProdDate and selected top {len(self.X_test_seq)} rows")

        self.X_test_seq = derive_chemistry_scrap_mix(self.X_test_seq, self.scrap_cols, self.cfg.target_chem)
        self.X_test_seq, self.scaler = scale_planning_data(
            self.X_test_seq,
            self.scrap_cols,
            mode=self.cfg.apply_scaling_mode,
            scaler_type=self.cfg.scaler_type,
        )

    def save_input_heats_passed(self):
        """Save the rows actually passed into the KF into a dated cumulative excel file."""
        date_s = datetime.now().strftime("%Y%m%d")
        # fname = self.cfg.output_dir / f"KF_input_heats_{self.cfg.target_chem}_{date_s}.xlsx"
        #Keep all original columns and add ProcessedDate at the end
        to_save = self.X_test_seq.copy()
        to_save["ProcessedDate"] = pd.Timestamp.now().normalize()
        # if fname.exists():
        #     old = pd.read_excel(fname)

        #     #Fix: standardize dtype
        #     old["ProcessedDate"] = pd.to_datetime(old["ProcessedDate"]).dt.normalize()
        #     to_save["ProcessedDate"] = pd.to_datetime(to_save["ProcessedDate"]).dt.normalize()

        #     combined = pd.concat([old, to_save], ignore_index=True)
        #     combined.to_excel(fname, index=False)
        # else:
        #     to_save.to_excel(fname, index=False)


    def initialize_kalman_state(self):
        n_scraps = len(self.scrap_cols)
        model_coefs = getattr(self.selected_model, "coef_", None)

        if model_coefs is None:
            raise ValueError("Selected model has no attribute 'coef_'")

        model_coefs = np.asarray(model_coefs, dtype=float).flatten()

        est = np.full(n_scraps, np.nan)
        m = min(len(model_coefs), n_scraps)
        est[:m] = model_coefs[:m]

        coef_df = pd.DataFrame({
            "Scrap_Name": self.scrap_cols,
            f"{self.cfg.target_chem}_estimated": est
        })

        limits = self.scrap_limits_df.drop(["Scrap Category", "Scrap Type"], axis=1)

        coef_df = coef_df.merge(limits, left_on="Scrap_Name", right_on="Scrap Type Ref", how="left")

        coef_df[self.cfg.chem_min] = coef_df[self.cfg.chem_min].fillna(0)
        coef_df[self.cfg.chem_max] = coef_df[self.cfg.chem_max].fillna(1e6)

        est_col = f"{self.cfg.target_chem}_estimated"
        coef_df[est_col] = coef_df[est_col].fillna(coef_df[self.cfg.chem_max])

        capped_col = f"{self.cfg.target_chem}_capped"
        coef_df[capped_col] = coef_df[est_col].clip(coef_df[self.cfg.chem_min], coef_df[self.cfg.chem_max])

        coef_df = coef_df.set_index("Scrap_Name").reindex(self.scrap_cols).reset_index()

        self.coef_df = coef_df
        model_x0 = coef_df[capped_col].values.astype(float).reshape(-1, 1)


        # If requested, try to load last row from previous kf coef file and use it as initial state_x
        if self.cfg.use_previous_kf:
            date_s = datetime.now().strftime("%Y%m%d")
            prev_fname_pattern = self.cfg.output_dir / f"kf_coef_df_{self.cfg.target_chem}_*.xlsx"
            # simple check: look for any file starting with kf_coef_df_{chem}_ (pick latest modified)
            candidates = list(self.cfg.output_dir.glob(f"kf_coef_df_{self.cfg.target_chem}_*.xlsx"))
            if candidates:
                latest = max(candidates, key=lambda p: p.stat().st_mtime)
                try:
                    prev_df = pd.read_excel(latest)
                    # Ensure scrap columns exist and take last row
                    if all(c in prev_df.columns for c in self.scrap_cols):
                        last_row = prev_df.iloc[-1]
                        x0_vals = last_row[self.scrap_cols].values.astype(float).reshape(-1, 1)
                        self.state_x = x0_vals
                    else:
                        self.state_x = model_x0
                except Exception:
                    self.state_x = model_x0
            else:
                self.state_x = model_x0
        else:
            self.state_x = model_x0

        # bounds
        self.lb = self.coef_df[self.cfg.chem_min].values.astype(float)
        self.ub = np.maximum(self.coef_df[self.cfg.chem_max].values.astype(float), self.lb + 1e-12)

        self.state_P = np.eye(len(self.state_x)) * (np.abs(self.state_x.flatten()) + 1e-4)
        self.state_Q = self.state_P * 0.01
        ml_residual = (self.X_test_seq[f"{self.cfg.target_chem}_lab"] - self.X_test_seq[self.cfg.target_chem]).dropna()
        if len(ml_residual) > 1:
            R_value = max(np.var(ml_residual) * 2, 1e-3)
        else:
            R_value = 1e-3
        self.state_R = np.array([[R_value]])

    def run_heatwise(self):
        handler = BroadcastHandler()
        with handler.applicationbound():
            boot  = logbook.Logger("Boot")
            rows = []
            for idx, row in self.X_test_seq.iterrows():
                heat_id = row.get("HeatID", idx)
                boot.info(f"Heat {int(idx+1)}/{len(self.X_test_seq)}: HeatID={heat_id}")
                print(f"Heat {int(idx+1)}/{len(self.X_test_seq)}: HeatID={heat_id}")

                W_frac = row[self.scrap_cols].astype(float).values
                C_meas = float(row[self.cfg.target_chem])
                if np.isnan(W_frac).any() or np.isnan(C_meas):
                    raise ValueError(f"NaN in heat {heat_id}")

                (
                    x_updated,
                    self.state_P,
                    self.state_Q,
                    self.state_R,
                    innovation,
                    innovation_uncertainty,
                    kalman_gain,
                    k_predicted,
                    error_rate,
                    prior_pred,
                ) = kalman_scrap_chemistry_update_bounded(
                    self.state_x,
                    self.state_P,
                    self.state_Q,
                    self.state_R,
                    W_frac,
                    C_meas,
                    self.lb,
                    self.ub,
                )

                self.state_x = x_updated.reshape(-1, 1)

                rows.append(
                    {
                        "HeatID": heat_id,
                        # "SequenceNum": row.get("Sequence Number"),
                        "SequenceNum": row.get("CastSeq"),
                        "GradeID": row.get("GradeID", None),
                        "GradeName": row.get("ProdGradeName", None),

                        f"{self.cfg.target_chem}_estimated": round(row[f"{self.cfg.target_chem}"], 3),
                        f"{self.cfg.target_chem}_lab": round(row[f"{self.cfg.target_chem}_lab"], 3),
                        "k_predicted_prior": prior_pred,
                        # "k_predicted": k_predicted,
                        f"{self.cfg.target_chem}_predicted": round(k_predicted,3),
                        "C_meas_used": C_meas,
                        "Innovation_value": innovation,
                        "Innovation_uncertainty": innovation_uncertainty,
                        "Kalman_gain": kalman_gain.tolist() if hasattr(kalman_gain, "tolist") else kalman_gain,
                        "updated_coefficients": self.state_x.flatten().tolist(),
                        "Error_rate_residual": round(error_rate, 3),
                        "P_trace": float(np.trace(self.state_P)),
                        "Q_trace": float(np.trace(self.state_Q)),
                        "R_value": float(self.state_R[0, 0]),
                    }
                )

                self.kalman_df_bound = pd.DataFrame(rows)
                # heat-wise append output (if desired)
                # partial = self.cfg.output_dir / f"kalman_df_bound_partial_heat_{int(idx)+1:03d}.xlsx" 
                # self.kalman_df_bound.to_excel(partial, index=False) # Uncomment above line to save after each heat (can generate many files)
            #Round small coefficient values to 0 for cleaner output (optional)
            self.kalman_df_bound["updated_coefficients"] = self.kalman_df_bound["updated_coefficients"].apply(
                lambda lst: [0.0 if abs(float(v)) < 1e-2 else float(v) for v in lst]
            )

            self.kalman_df_bound["Error_rate_percent"] = (
                    self.kalman_df_bound["Error_rate_residual"] / self.kalman_df_bound["C_meas_used"].replace(0, np.nan) * 100
            )

            self.kalman_df_bound["Error_rate_percent"] = round(self.kalman_df_bound["Error_rate_percent"], 3)


    def plot_predicted_vs_actual(self, out_df_path: Optional[Path] = None, df: pd.DataFrame = None, save_name: Optional[str] = None):
        # load dataframe if path provided, else use in-memory results
        if df is None:
            if out_df_path is not None and out_df_path.exists():
                df = pd.read_excel(out_df_path)
            else:
                df = self.kalman_df_bound.copy()

        pred_col = f"{self.cfg.target_chem}_predicted" # "k_predicted"
        actual_col = f"{self.cfg.target_chem}_estimated" #self.cfg.target_chem

        if pred_col not in df.columns or actual_col not in df.columns:
            raise ValueError(f"Required columns not found in data: '{pred_col}' or '{actual_col}'")

        df = df.dropna(subset=[pred_col, actual_col]).copy()
        preds = pd.to_numeric(df[pred_col], errors="coerce").astype(float).values
        actuals = pd.to_numeric(df[actual_col], errors="coerce").astype(float).values

        if len(preds) == 0:
            raise ValueError("No valid rows to plot (after dropping NaNs)")

        residuals = actuals - preds
        std_r = np.nanstd(residuals)
        thresh = 3.0 * std_r if std_r > 0 else 0
        outlier_mask = np.abs(residuals) > thresh

        # --- INSERT HERE: save outliers + annotated DF ---
        df = df.reset_index(drop=True).copy()
        df["is_outlier"] = outlier_mask
        date_s = datetime.now().strftime("%Y%m%d_%H%M%S")
        outliers = df.loc[df["is_outlier"]].copy()
        # if not outliers.empty:
        #     out_file = self.cfg.output_dir / f"pred_vs_actual_outliers_{self.cfg.target_chem}_{date_s}.xlsx"
        #     outliers.to_excel(out_file, index=False)
        #     print(f"Saved outliers: {out_file} (count={len(outliers)})")
        # annotated_file = self.cfg.output_dir / f"pred_vs_actual_annotated_{self.cfg.target_chem}_{date_s}.xlsx"
        # df.to_excel(annotated_file, index=False)

        fig, ax = plt.subplots(figsize=(7, 7))

        # draw all points in blue
        ax.scatter(preds, actuals, color="tab:blue", alpha=0.6, label="Data")

        # highlight outliers with red filled circles on top
        if outlier_mask.any():
            ax.scatter(preds[outlier_mask], actuals[outlier_mask],
                    color="red", edgecolor="k", s=70, marker="o",
                    label=f"Outliers ({outlier_mask.sum()})", zorder=5)

        # diagonal y=x line and set symmetric limits so plot matches manual range
        mn = np.nanmin(np.concatenate([preds, actuals]))
        mx = np.nanmax(np.concatenate([preds, actuals]))
        pad = (mx - mn) * 0.03 if mx > mn else 0.01
        ax.plot([mn - pad, mx + pad], [mn - pad, mx + pad], color="gray", linestyle="--", linewidth=1)
        ax.set_xlim(mn - pad, mx + pad)
        ax.set_ylim(mn - pad, mx + pad)

        ax.set_xlabel(f"Predicted ({pred_col})")
        ax.set_ylabel(f"Actual ({actual_col})")
        ax.set_title(f"Predicted vs Actual — {self.cfg.target_chem}")
        ax.legend()
        ax.grid(True)

        if save_name is None:
            save_name = self.cfg.output_dir / f"pred_vs_actual_{self.cfg.target_chem}.png"
        else:
            save_name = Path(save_name)
        # fig.savefig(save_name, bbox_inches="tight", dpi=150)
        plt.close(fig)
        return save_name, int(outlier_mask.sum())

    def save_results(self):
        date_s = datetime.now().strftime("%Y%m%d")

        def _heat_id_for_fname(hid):
            if hid is None or (isinstance(hid, float) and np.isnan(hid)):
                return "unknown"
            try:
                return str(int(float(hid)))
            except (ValueError, TypeError):
                s = str(hid).strip()
                for c in '<>:"/\\|?*':
                    s = s.replace(c, "_")
                return s[:120] if len(s) > 120 else s

        cols_order = [
            "HeatID","SequenceNum", "GradeID", "GradeName",
            f"{self.cfg.target_chem}_estimated", f"{self.cfg.target_chem}_lab",
            f"{self.cfg.target_chem}_predicted", "Error_rate_residual",  "Error_rate_percent"
        ]
        #Create missing cols to avoid errors
        for c in cols_order:
            if c not in self.kalman_df_bound.columns:
                self.kalman_df_bound[c] = np.nan
        kalman_out = self.kalman_df_bound[cols_order]

        tc = self.cfg.target_chem
        out_df_path = self.cfg.output_dir / f"KF_{tc}_Prediction.xlsx"
        # Skip writing KF prediction workbooks; keep dataframe in memory.
        kalman_out = kalman_out.drop_duplicates().reset_index(drop=True)
        self.kf_prediction_df = kalman_out.copy()

        # One file per heat (HeatID + target chem in filename)
        # for _, row in kalman_out.iterrows():
        #     hid = _heat_id_for_fname(row.get("HeatID"))
        #     per_heat_path = self.cfg.output_dir / f"KF_{tc}_Prediction_Heat_{hid}.xlsx"
        #     row.to_frame().T.to_excel(per_heat_path, index=False)

        # generate and save prediction vs actual plot (call the new function)
        # try:
        #     img_path, n_outliers = self.plot_predicted_vs_actual(out_df_path=out_df_path)
        #     print(f"Saved pred vs actual plot: {img_path} (outliers={n_outliers})")
        # except Exception as e:
        #     print(f"Plot generation failed: {e}")

        # prepare coef df with scrap columns in specified order
        kf_coef = pd.DataFrame(self.kalman_df_bound["updated_coefficients"].tolist(), columns=self.scrap_cols)
       
        kf_coef.insert(0, "GradeName", self.kalman_df_bound.get("GradeName", pd.Series(np.nan)))
        kf_coef.insert(0, "GradeID", self.kalman_df_bound.get("GradeID", pd.Series(np.nan)))
        kf_coef.insert(0, "SequenceNum", self.kalman_df_bound.get("SequenceNum", pd.Series(np.nan)))
        kf_coef.insert(0, "HeatID", self.kalman_df_bound.get("HeatID", pd.Series(np.nan)))

        kf_coef[self.scrap_cols] = kf_coef[self.scrap_cols].round(3) #Added this line to round coefficients for cleaner output
        self.kf_coef_df = kf_coef.copy()

        # out_coef_path = self.cfg.output_dir / f"KF_Scrap_Type_Predictions_{self.cfg.target_chem}_{date_s}.xlsx"
        # if out_coef_path.exists():
        #     old = pd.read_excel(out_coef_path)
        #     combined = pd.concat([old, kf_coef], ignore_index=True)
        #     combined = combined.drop_duplicates()
        #     combined.to_excel(out_coef_path, index=False)
        # else:
        #     kf_coef = kf_coef.drop_duplicates()
        #     kf_coef.to_excel(out_coef_path, index=False)

        # -----------------------------
        # Save output based on input type
        # -----------------------------
        input_ext = getattr(self.cfg, "input_ext", ".xlsx")

        # Decide file path
        if input_ext == ".csv":
            out_coef_path = self.cfg.output_dir / f"KF_Scrap_Type_Predictions_{tc}.csv"
        else:
            out_coef_path = self.cfg.output_dir / f"KF_Scrap_Type_Predictions_{tc}.xlsx"

        # -----------------------------
        # Write logic (append + deduplicate)
        # -----------------------------
        # if out_coef_path.exists():
        #
        #     if input_ext == ".csv":
        #         enc = getattr(self.cfg, "csv_encoding", None)
        #         old = read_csv_auto(out_coef_path, preferred_encoding=enc)
        #     else:
        #         old = pd.read_excel(out_coef_path)
        #
        #     combined = pd.concat([old, kf_coef], ignore_index=True)
        #     combined = combined.drop_duplicates()
        #
        #     if input_ext == ".csv":
        #         combined.to_csv(out_coef_path, index=False)
        #     else:
        #         combined.to_excel(out_coef_path, index=False)
        #
        # else:
        #     kf_coef = kf_coef.drop_duplicates()
        #
        #     if input_ext == ".csv":
        #         kf_coef.to_csv(out_coef_path, index=False)
        #     else:
        #         kf_coef.to_excel(out_coef_path, index=False)
        kf_coef = kf_coef.drop_duplicates().reset_index(drop=True)

        # Per-heat scrap-type coefficient rows
        # for _, crow in kf_coef.iterrows():
        #     hid = _heat_id_for_fname(crow.get("HeatID"))
        #     if input_ext == ".csv":
        #         ph = self.cfg.output_dir / f"KF_Scrap_Type_Predictions_{tc}_Heat_{hid}.csv"
        #         crow.to_frame().T.to_csv(ph, index=False)
        #     else:
        #         ph = self.cfg.output_dir / f"KF_Scrap_Type_Predictions_{tc}_Heat_{hid}.xlsx"
        #         crow.to_frame().T.to_excel(ph, index=False)

        template_path = Path(getattr(self.cfg, "template_path", BASE_DIR / "Uploads" / "Recom_Scrap_Input_3 1.xlsx"))
        if template_path.exists():
            try:
                row_meta = {"HeatID", "SequenceNum", "GradeID", "GradeName"}

                def _norm_scrap(s: str) -> str:
                    return " ".join(str(s).strip().split())

                def _strip_chg_prefix(x: str) -> str:
                    t = str(x).strip()
                    if t.upper().startswith("CHG"):
                        t = t[3:].lstrip("- ").lstrip()
                    return t

                #for i in range(len(kf_coef)):
                # ONLY PROCESS LAST HEAT
                i = len(kf_coef) - 1

                if i >= 0:
                    hid = _heat_id_for_fname(kf_coef.iloc[i].get("HeatID"))
                    heat_out_path = self.cfg.output_dir / f"KF_Scarp_Chemistry_File_{hid}.xlsx"
                    pred_row = kf_coef.iloc[i]

                    source_book_path = heat_out_path if heat_out_path.exists() else template_path
                    inp = pd.read_excel(source_book_path, sheet_name="Input").copy()
                    template_inp = pd.read_excel(template_path, sheet_name="Input")

                    output_cols = [
                        "Scrap_Type", "Category", "Maximum_Usage", "Cost", "Yield",
                        "Yielded_Cost", "Inventory", "Fe", "C", "Cu", "Ni", "Cr", "Mo",
                        "Sn", "Si", "Mn", " Power_Cost ()", "Flux+C ()",
                    ]
                    template_to_output = {
                        "Scrap Category": "Category",
                        "Purchase Cost": "Cost",
                        "Metallic Yield Cost": "Yielded_Cost",
                        "Power Cost @ 0.0504$ / KWH": " Power_Cost ()",
                        "Flux and Carbon Cost (31 +/- 6 $)": "Flux+C ()",
                        "Mb": "Mo",
                        "Max Quantity available (NT)": "Inventory",
                        "Scrap Type": "Scrap_Type",
                    }

                    if "Scrap Type" not in inp.columns and "Scrap_Type" in inp.columns:
                        inp = inp.rename(columns={"Scrap_Type": "Scrap Type"})
                    if "Inventory" in inp.columns and "Max Quantity available (NT)" not in inp.columns:
                        inp = inp.rename(columns={"Inventory": "Max Quantity available (NT)"})

                    allowed_input_cols = set(template_inp.columns.tolist()) | set(output_cols) | {tc}

                    for c in ("HeatID", "target_chem", "KF_output_date"):
                        if c in inp.columns:
                            inp = inp.drop(columns=[c])
                    inp = inp[[c for c in inp.columns if c in allowed_input_cols]]

                    if "Scrap_Type_New" not in inp.columns:
                        scrap_col = "Scrap Type" if "Scrap Type" in inp.columns else None
                        if scrap_col is None:
                            raise ValueError("Input sheet must contain 'Scrap_Type_New' or 'Scrap Type'")
                        key_map = dict(zip(
                            template_inp["Scrap Type"].astype(str).map(_norm_scrap),
                            template_inp["Scrap_Type_New"],
                        ))
                        inp["Scrap_Type_New"] = inp[scrap_col].astype(str).map(_norm_scrap).map(key_map)

                    if tc not in inp.columns:
                        inp[tc] = np.nan

                    def _mask_for_chg(chg_key: str) -> pd.Series:
                        key = _norm_scrap(chg_key)
                        stn = inp["Scrap_Type_New"].astype(str).map(_norm_scrap)
                        m = stn == key
                        if m.any():
                            return m
                        st_suf = stn.map(_strip_chg_prefix).map(_norm_scrap)
                        key_suf = _norm_scrap(_strip_chg_prefix(key))
                        m = st_suf == key_suf
                        if m.any():
                            return m
                        for scrap_col in ("Scrap Type", "Scrap_Type"):
                            if scrap_col in inp.columns:
                                st = inp[scrap_col].astype(str).map(_norm_scrap).map(_strip_chg_prefix)
                                m = st == key_suf
                                if m.any():
                                    return m
                        return m

                    for col_name, val in pred_row.items():
                        if col_name in row_meta:
                            continue
                        col_stripped = str(col_name).strip()
                        num = pd.to_numeric(val, errors="coerce")
                        if pd.isna(num):
                            continue
                        num_f = float(num)

                        mask = _mask_for_chg(col_stripped)
                        if not mask.any():
                            continue
                        if col_stripped in inp.columns:
                            inp.loc[mask, col_stripped] = num_f
                        inp.loc[mask, tc] = num_f

                    if "Scrap_Type_New" in inp.columns:
                        inp = inp.drop(columns=["Scrap_Type_New"])

                    # Prefer output column names; drop template aliases only in memory before writing.
                    for template_name, output_name in template_to_output.items():
                        if template_name in inp.columns and output_name in inp.columns:
                            inp = inp.drop(columns=[template_name])

                    inp = inp.rename(columns={k: v for k, v in template_to_output.items() if k in inp.columns})
                    inp = inp.reindex(columns=output_cols)

                    with pd.ExcelWriter(heat_out_path, engine="openpyxl") as writer:
                        inp.to_excel(writer, sheet_name="Input", index=False)

                    handler = BroadcastHandler()
                    with handler.applicationbound():
                        boot  = logbook.Logger("Boot")
                        boot.info(f"Updated per-heat workbook: {heat_out_path}")
                    print(f"Updated per-heat workbook: {heat_out_path}")

                    return heat_out_path
            except Exception as e:
                handler = BroadcastHandler()
                with handler.applicationbound():
                    boot  = logbook.Logger("Boot")
                    boot.info(f"Could not create/update per-heat workbook: {e}")
                print(f"Could not create/update per-heat workbook: {e}")

        #Saving metric results into Json
        # metrics_df = self.evaluate_kalman_metrics(self.kalman_df_bound)
        # metrics_json_path = self.cfg.output_dir / f"KF_performance_metrics_{self.cfg.target_chem}_{date_s}.json"
        # save_metrics_json(metrics_df, metrics_json_path, self.cfg.target_chem)

    def run(self):
        self.prepare()
        self.preprocess()
        self.save_input_heats_passed()
        self.initialize_kalman_state()
        self.run_heatwise()
        # self.save_results()
        # print("Done: Kalman filter pipeline complete.")
        output_file = self.save_results()
        handler = BroadcastHandler()
        with handler.applicationbound():
            boot  = logbook.Logger("Boot")
            boot.info("Done: Kalman filter pipeline complete.")
            _broadcast(_DONE)
        print("Done: Kalman filter pipeline complete.")
        

        return output_file





# %%
