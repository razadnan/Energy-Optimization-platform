"""
Data Preprocessing Module (Multi-Tenant SaaS)
Energy Optimization Agent
"""

import pandas as pd
from backend.config import config
from backend.database import DatabaseManager
from services.logger import setup_logger

logger = setup_logger("Preprocessing")


class DataPreprocessor:
    """
    Handles loading, validating, cleaning, feature engineering,
    and saving the energy consumption datasets.
    """

    def __init__(self, file_path=None):
        self.file_path = file_path or (
            config.RAW_DATA_DIR /
            "household_power_consumption.txt"
        )

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> tuple[bool, list[str]]:
        """
        Validates the dataset against required checks:
        ✓ Missing values
        ✓ Wrong timestamps
        ✓ Negative power
        ✓ Duplicate rows
        ✓ Empty columns
        ✓ Invalid datatype
        """
        errors = []

        # 1. Check for completely empty columns
        empty_cols = [col for col in df.columns if df[col].isnull().all()]
        if empty_cols:
            errors.append(f"Columns are completely empty: {', '.join(empty_cols)}")

        # 2. Check for Timestamp / Date-Time column
        ts_col = None
        for col in ["Datetime", "datetime", "Timestamp", "timestamp", "date_time"]:
            if col in df.columns:
                ts_col = col
                break
        
        # If no combined Datetime, check if we have separate Date and Time
        has_date_time = ("Date" in df.columns or "date" in df.columns) and ("Time" in df.columns or "time" in df.columns)
        if ts_col is None and not has_date_time:
            errors.append("Missing timestamp column (expected Date and Time, Datetime, or Timestamp).")

        # 3. Check for Active Power column
        power_col = None
        for col in ["Global_active_power", "active_power", "Power", "power", "Consumption", "consumption", "Usage", "usage"]:
            if col in df.columns:
                power_col = col
                break
        if power_col is None:
            errors.append("Missing Active Power consumption column (expected Global_active_power, Power, or Usage).")

        if errors:
            return False, errors

        # 4. Detailed row-by-row checks (limit to first 5 errors to prevent huge payload)
        max_errors = 5
        
        # Row verification
        for idx, row in df.iterrows():
            row_num = idx + 2 # 1-based + header row
            
            # Check Active Power
            val = row[power_col]
            if pd.isnull(val) or str(val).strip() == "" or str(val).strip() == "?":
                errors.append(f"Row {row_num}: Active Power is missing.")
            else:
                try:
                    num_val = float(val)
                    if num_val < 0:
                        errors.append(f"Row {row_num}: Negative power consumption detected ({num_val} kW).")
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid datatype for Active Power ('{val}').")

            if len(errors) >= max_errors:
                break

            # Check Voltage if present
            voltage_col = next((c for c in ["Voltage", "voltage", "V", "v"] if c in df.columns), None)
            if voltage_col:
                v_val = row[voltage_col]
                if pd.isnull(v_val) or str(v_val).strip() == "" or str(v_val).strip() == "?":
                    errors.append(f"Row {row_num}: Voltage is missing.")
                else:
                    try:
                        v_num = float(v_val)
                        if v_num < 0:
                            errors.append(f"Row {row_num}: Negative voltage detected ({v_num} V).")
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid datatype for Voltage ('{v_val}').")

            if len(errors) >= max_errors:
                break

        # Check for wrong timestamps/chronology if Datetime column is parseable
        if not errors:
            try:
                if ts_col:
                    dates = pd.to_datetime(df[ts_col], errors="coerce")
                else:
                    date_col = "Date" if "Date" in df.columns else "date"
                    time_col = "Time" if "Time" in df.columns else "time"
                    dates = pd.to_datetime(df[date_col].astype(str) + " " + df[time_col].astype(str), errors="coerce")
                
                if dates.isnull().any():
                    null_idx = dates[dates.isnull()].index[0]
                    errors.append(f"Row {null_idx + 2}: Invalid or unparseable Datetime format.")
            except Exception as e:
                errors.append(f"Datetime formatting error: {str(e)}")

        if errors:
            return False, errors
        return True, []

    @staticmethod
    def clean_and_standardize(df: pd.DataFrame) -> pd.DataFrame:
        """
        Automatically:
        ✓ Remove duplicates
        ✓ Fill missing values
        ✓ Convert timestamps
        ✓ Convert units / standard names
        ✓ Normalize values
        """
        df_clean = df.copy()

        # 1. Map Datetime
        ts_col = next((c for c in ["Datetime", "datetime", "Timestamp", "timestamp", "date_time"] if c in df_clean.columns), None)
        if ts_col:
            df_clean["Datetime"] = pd.to_datetime(df_clean[ts_col], errors="coerce")
        else:
            date_col = "Date" if "Date" in df_clean.columns else "date"
            time_col = "Time" if "Time" in df_clean.columns else "time"
            df_clean["Datetime"] = pd.to_datetime(
                df_clean[date_col].astype(str) + " " + df_clean[time_col].astype(str),
                errors="coerce"
            )

        # 2. Map Power column
        power_col = next((c for c in ["Global_active_power", "active_power", "Power", "power", "Consumption", "consumption", "Usage", "usage"] if c in df_clean.columns), None)
        df_clean["Global_active_power"] = pd.to_numeric(df_clean[power_col], errors="coerce")

        # 3. Map other standard fields or create defaults
        cols_to_map = {
            "Global_reactive_power": ["Global_reactive_power", "reactive_power", "Reactive_Power", "reactive"],
            "Voltage": ["Voltage", "voltage", "Volt", "volt", "V"],
            "Global_intensity": ["Global_intensity", "intensity", "Intensity", "Current", "current", "A"],
            "Sub_metering_1": ["Sub_metering_1", "sub_metering_1", "kitchen", "Kitchen", "sub1"],
            "Sub_metering_2": ["Sub_metering_2", "sub_metering_2", "laundry", "Laundry", "sub2"],
            "Sub_metering_3": ["Sub_metering_3", "sub_metering_3", "hvac", "HVAC", "sub3"],
        }
        
        for std_name, aliases in cols_to_map.items():
            found_col = next((alias for alias in aliases if alias in df_clean.columns), None)
            if found_col:
                df_clean[std_name] = pd.to_numeric(df_clean[found_col], errors="coerce")
            else:
                if std_name == "Voltage":
                    df_clean["Voltage"] = 230.0
                else:
                    df_clean[std_name] = 0.0

        # Fill any NaNs in standard columns
        for col in ["Global_active_power", "Global_reactive_power", "Voltage", "Global_intensity", 
                    "Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]:
            df_clean[col] = df_clean[col].fillna(df_clean[col].median() if not df_clean[col].isna().all() else 0.0)

        # Drop duplicates
        df_clean = df_clean.drop_duplicates()

        # Drop rows with invalid Datetime
        df_clean = df_clean.dropna(subset=["Datetime"])

        # Sort chronological
        df_clean = df_clean.sort_values("Datetime")

        # Select standard columns
        std_columns = [
            "Datetime", "Global_active_power", "Global_reactive_power",
            "Voltage", "Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3"
        ]
        return df_clean[std_columns]

    def preprocess_file(self, file_path: str, dataset_id: int) -> pd.DataFrame:
        """
        Loads, validates, cleans, and engineers features for a specific file,
        then saves the result to the database under the given dataset_id.
        """
        logger.info(f"Preprocessing file: {file_path} for dataset {dataset_id}")
        
        # Load file (supports CSV, XLS, XLSX)
        if file_path.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path, na_values=["?"])
        else:
            df = pd.read_csv(file_path, sep=None, engine="python", na_values=["?"])

        # Validate
        is_valid, errors = self.validate_dataframe(df)
        if not is_valid:
            error_msg = "; ".join(errors)
            logger.error(f"Validation failed: {error_msg}")
            raise ValueError(error_msg)

        # Clean
        df = self.clean_and_standardize(df)

        # Feature Engineering
        from services.feature_engineering import FeatureEngineer
        df = FeatureEngineer.create_features(df)

        # Save to database
        DatabaseManager.save_data(df, dataset_id)
        
        logger.info(f"Preprocessing complete for dataset {dataset_id}.")
        return df