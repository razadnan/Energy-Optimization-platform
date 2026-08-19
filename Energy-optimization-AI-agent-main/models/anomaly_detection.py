"""
=========================================================
Anomaly Detection Model
Energy Optimization Agent
=========================================================
"""

import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.config import config
from backend.database import DatabaseManager
from services.logger import setup_logger

logger = setup_logger("AnomalyDetection")


class AnomalyDetectionModel:
    """
    Isolation Forest based anomaly detection model.
    """

    def __init__(self, dataset_id: int = None):
        self.dataset_id = dataset_id
        self.file_path = (
            config.PROCESSED_DATA_DIR /
            "processed_energy_data.csv"
        )
        self.df = None
        self.features = None
        self.model = None
        self.results = None

    # =====================================================
    # LOAD DATA
    # =====================================================

    def load_data(self):
        logger.info(f"Loading processed dataset from database for dataset_id {self.dataset_id}...")
        self.df = DatabaseManager.get_data(self.dataset_id)
        logger.info(
            f"Loaded {len(self.df):,} records."
        )
        return self.df

    # =====================================================
    # PREPARE FEATURES
    # =====================================================

    def prepare_features(self):

        logger.info("Preparing feature matrix...")

        feature_columns = [

            "Global_active_power",

            "Global_reactive_power",

            "Voltage",

            "Global_intensity",

            "Sub_metering_1",

            "Sub_metering_2",

            "Sub_metering_3"

        ]

        self.features = self.df[
            feature_columns
        ].copy()

        logger.info(
            f"Feature Matrix Shape : "
            f"{self.features.shape}"
        )

        return self.features

    # =====================================================
    # BUILD MODEL
    # =====================================================

    def build_model(self):

        logger.info(
            "Building Isolation Forest..."
        )

        self.model = IsolationForest(

            n_estimators=150,

            contamination=0.01,

            random_state=42,

            n_jobs=-1

        )

        return self.model

    # =====================================================
    # TRAIN MODEL
    # =====================================================

    def train_model(self):

        logger.info("=" * 60)
        logger.info("Training Isolation Forest")
        logger.info("=" * 60)

        self.model.fit(
            self.features
        )

        logger.info(
            "Training completed."
        )

        return self.model
    
        # =====================================================
    # DETECT ANOMALIES
    # =====================================================

    def detect_anomalies(self):
        """
        Detect anomalies using Isolation Forest.
        """

        logger.info("Detecting anomalies...")

        predictions = self.model.predict(
            self.features
        )

        scores = self.model.decision_function(
            self.features
        )

        self.results = self.df.copy()

        self.results["Anomaly"] = predictions

        self.results["Anomaly_Score"] = scores

        # Add severity tiering
        self.results["Severity"] = "Normal"
        anomalies_mask = self.results["Anomaly"] == -1
        if anomalies_mask.any():
            anomaly_scores = self.results.loc[anomalies_mask, "Anomaly_Score"]
            q25 = anomaly_scores.quantile(0.25)
            q75 = anomaly_scores.quantile(0.75)
            
            self.results.loc[anomalies_mask & (self.results["Anomaly_Score"] < q25), "Severity"] = "Critical"
            self.results.loc[anomalies_mask & (self.results["Anomaly_Score"] >= q25) & (self.results["Anomaly_Score"] < q75), "Severity"] = "High"
            self.results.loc[anomalies_mask & (self.results["Anomaly_Score"] >= q75), "Severity"] = "Medium"

        anomaly_count = int(
            (predictions == -1).sum()
        )

        logger.info(
            f"Detected {anomaly_count:,} anomalies."
        )

        return self.results

    # =====================================================
    # ANOMALY STATISTICS
    # =====================================================

    def anomaly_statistics(self):
        """
        Generate anomaly statistics.
        """

        logger.info(
            "Generating anomaly statistics..."
        )

        total_records = len(self.results)

        anomaly_records = int(
            (self.results["Anomaly"] == -1).sum()
        )

        normal_records = int(
            (self.results["Anomaly"] == 1).sum()
        )

        anomaly_percent = round(
            anomaly_records /
            total_records * 100,
            2
        )

        critical_count = int((self.results["Severity"] == "Critical").sum())
        high_count = int((self.results["Severity"] == "High").sum())
        medium_count = int((self.results["Severity"] == "Medium").sum())

        return {

            "total_records":
                total_records,

            "normal_records":
                normal_records,

            "anomaly_records":
                anomaly_records,

            "anomaly_percentage":
                anomaly_percent,

            "critical_anomalies":
                critical_count,

            "high_anomalies":
                high_count,

            "medium_anomalies":
                medium_count

        }

    # =====================================================
    # HOURLY ANALYSIS
    # =====================================================

    def hourly_anomaly_analysis(self):
        """
        Analyze anomalies by hour.
        """

        logger.info(
            "Analyzing hourly anomalies..."
        )

        anomalies = self.results[
            self.results["Anomaly"] == -1
        ]

        hourly = (

            anomalies

            .groupby("Hour")

            .size()

            .sort_index()

        )

        return hourly.to_dict()

    # =====================================================
    # DAILY ANALYSIS
    # =====================================================

    def daily_anomaly_analysis(self):
        """
        Analyze anomalies by weekday.
        """

        logger.info(
            "Analyzing weekday anomalies..."
        )

        anomalies = self.results[
            self.results["Anomaly"] == -1
        ]

        daily = (

            anomalies

            .groupby("Weekday")

            .size()

            .sort_values(
                ascending=False
            )

        )

        return daily.to_dict()

    # =====================================================
    # HIGH RISK RECORDS
    # =====================================================

    def highest_risk_records(self):
        """
        Return highest-risk anomaly records.
        """

        logger.info(
            "Selecting highest-risk anomalies..."
        )

        high_risk = (

            self.results

            [

                self.results["Anomaly"] == -1

            ]

            .sort_values(
                by="Anomaly_Score"
            )

            .head(10)

        )

        columns = [

            "Datetime",

            "Global_active_power",

            "Voltage",

            "Global_intensity",

            "Anomaly_Score",

            "Severity"

        ]

        return high_risk[
            columns
        ]
    
        # =====================================================
    # SAVE RESULTS
    # =====================================================

    def save_results(
        self,
        filename="anomaly_detection_results.csv"
    ):
        """
        Save anomaly detection results.
        """

        logger.info(
            "Saving anomaly detection results..."
        )

        output_path = (
            config.OUTPUT_DIR /
            filename
        )

        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        self.results.to_csv(
            output_path,
            index=False
        )

        logger.info(
            f"Results saved to {output_path}"
        )

        return output_path

    # =====================================================
    # GENERATE REPORT
    # =====================================================

    def generate_report(self):
        """
        Generate complete anomaly detection report.
        """

        logger.info("=" * 60)
        logger.info("Generating Anomaly Detection Report")
        logger.info("=" * 60)

        report = {

            "statistics":
                self.anomaly_statistics(),

            "hourly_analysis":
                self.hourly_anomaly_analysis(),

            "daily_analysis":
                self.daily_anomaly_analysis(),

            "high_risk_records":
                self.highest_risk_records()

        }

        logger.info(
            "Anomaly report generated successfully."
        )

        return report

    # =====================================================
    # COMPLETE PIPELINE
    # =====================================================

    def save_anomalies_to_db(self):
        """Save the detected anomalies into SQLite alerts table."""
        if self.results is None or self.dataset_id is None:
            return
        logger.info(f"Saving anomalies to database for dataset {self.dataset_id}...")
        anomalies = self.results[self.results["Anomaly"] == -1]
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM alerts WHERE dataset_id = ?", (self.dataset_id,))
            conn.commit()
            
            for _, row in anomalies.iterrows():
                dt_str = str(row["Datetime"])
                severity = str(row["Severity"])
                active_power = float(row["Global_active_power"])
                description = f"Anomaly detected on {dt_str}: Active power is abnormal ({active_power:.2f} kW)."
                
                cursor.execute(
                    """
                    INSERT INTO alerts (dataset_id, timestamp, type, severity, value, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.dataset_id,
                        dt_str,
                        "Anomaly",
                        severity,
                        active_power,
                        description
                    )
                )
            conn.commit()
            logger.info("Anomalies saved to database successfully.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save anomalies to database: {e}")
        finally:
            conn.close()

    def run_pipeline(self):
        """
        Execute the complete anomaly detection pipeline.
        """

        logger.info("=" * 60)
        logger.info("Starting Anomaly Detection Pipeline")
        logger.info("=" * 60)

        self.load_data()

        self.prepare_features()

        self.build_model()

        self.train_model()

        self.detect_anomalies()

        self.save_anomalies_to_db()

        self.save_results()

        report = self.generate_report()

        logger.info("=" * 60)
        logger.info("Pipeline Completed Successfully")
        logger.info("=" * 60)

        return report


# =====================================================
# STANDALONE EXECUTION
# =====================================================

if __name__ == "__main__":

    detector = AnomalyDetectionModel()

    report = detector.run_pipeline()

    print("\nANOMALY STATISTICS")
    print(report["statistics"])

    print("\nTOP HIGH RISK RECORDS")
    print(report["high_risk_records"])

    print("\nAnomaly Detection Completed Successfully.")