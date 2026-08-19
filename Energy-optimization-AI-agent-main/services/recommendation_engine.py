"""
=========================================================
Recommendation Engine
Energy Optimization Agent
=========================================================
"""

from services.logger import setup_logger
from backend.database import DatabaseManager

logger = setup_logger("RecommendationEngine")


class RecommendationEngine:
    """
    Generates intelligent energy-saving recommendations
    using analytics, forecasting and anomaly detection.
    """

    def __init__(
        self,
        usage_report,
        forecast_report,
        anomaly_report,
        dataset_id: int = None
    ):

        import pandas as pd

        self.usage = usage_report or {}
        self.forecast = forecast_report or {}
        if isinstance(self.forecast, dict) and "forecast" in self.forecast:
            if isinstance(self.forecast["forecast"], list):
                self.forecast["forecast"] = pd.DataFrame(self.forecast["forecast"])
        self.anomaly = anomaly_report or {}
        self.dataset_id = dataset_id

        self.recommendations = []

    def _safe_float(self, val, default=0.0):
        if val is None:
            return default
        try:
            import math
            fval = float(val)
            if math.isnan(fval) or math.isinf(fval):
                return default
            return fval
        except (ValueError, TypeError):
            return default

    # =====================================================
    # PEAK USAGE
    # =====================================================

    def peak_hour_recommendations(self):
        """
        Generate recommendations based on peak usage.
        """

        logger.info(
            "Analyzing peak hour usage..."
        )

        peak_usage = self.usage.get("peak_usage", {})
        if not peak_usage:
            return self.recommendations

        peak_hour = peak_usage.get("peak_hour")
        peak_power = peak_usage.get("peak_hour_average_kw")

        if peak_hour is None or peak_power is None:
            return self.recommendations

        try:
            import math
            if math.isnan(peak_hour) or math.isnan(peak_power):
                return self.recommendations
        except Exception:
            return self.recommendations

        self.recommendations.append({

            "category":
                "Peak Usage",

            "priority":
                "High",

            "recommendation":
                f"Reduce appliance usage around "
                f"{int(peak_hour)}:00 when average "
                f"consumption reaches "
                f"{float(peak_power):.2f} kW.",

            "estimated_saving_percent":
                8

        })

        return self.recommendations

    # =====================================================
    # WEEKEND USAGE
    # =====================================================

    def weekend_recommendations(self):
        """
        Weekend usage recommendations.
        """

        logger.info(
            "Analyzing weekend usage..."
        )

        weekday_weekend = self.usage.get("weekday_weekend", {})
        if not weekday_weekend:
            return self.recommendations

        difference = weekday_weekend.get("difference_kw")
        difference = self._safe_float(difference)

        if difference > 0:

            self.recommendations.append({

                "category":
                    "Weekend Usage",

                "priority":
                    "Medium",

                "recommendation":
                    "Weekend consumption is higher "
                    "than weekday usage. Shift "
                    "heavy appliances to off-peak "
                    "hours whenever possible.",

                "estimated_saving_percent":
                    5

            })

        return self.recommendations
    
        # =====================================================
    # FORECAST RECOMMENDATIONS
    # =====================================================

    def forecast_recommendations(self):
        """
        Generate recommendations using forecast results.
        """

        logger.info(
            "Analyzing forecast..."
        )

        import pandas as pd
        forecast_df = self.forecast.get("forecast")
        if forecast_df is None:
            return self.recommendations
            
        if isinstance(forecast_df, list):
            forecast_df = pd.DataFrame(forecast_df)
            
        if not isinstance(forecast_df, pd.DataFrame) or forecast_df.empty:
            return self.recommendations

        average_forecast = round(
            self._safe_float(forecast_df["Predicted_Energy_kWh"].mean()),
            2
        )

        historical_average = self._safe_float(
            self.usage.get("consumption", {}).get("average_daily_energy_kwh")
        )

        if average_forecast > historical_average and historical_average > 0:

            increase = round(

                (
                    average_forecast
                    -
                    historical_average
                )
                /
                historical_average
                * 100,

                2

            )

            self.recommendations.append({

                "category":
                    "Forecast",

                "priority":
                    "High",

                "recommendation":
                    f"Forecasted daily energy "
                    f"consumption is expected to "
                    f"increase by {increase}% "
                    f"compared to historical "
                    f"usage. Reduce unnecessary "
                    f"loads during peak periods.",

                "estimated_saving_percent":
                    10

            })

        return self.recommendations

    # =====================================================
    # ANOMALY RECOMMENDATIONS
    # =====================================================

    def anomaly_recommendations(self):
        """
        Generate recommendations from anomalies.
        """

        logger.info(
            "Analyzing anomalies..."
        )

        statistics = self.anomaly.get("statistics", {})
        if not statistics:
            return self.recommendations

        anomaly_percent = statistics.get("anomaly_percentage")
        anomaly_percent = self._safe_float(anomaly_percent)

        if anomaly_percent > 0.5:

            self.recommendations.append({

                "category":
                    "Anomaly",

                "priority":
                    "High",

                "recommendation":
                    "Abnormal energy usage has "
                    "been detected. Inspect "
                    "electrical appliances for "
                    "faults or unnecessary "
                    "standby power consumption.",

                "estimated_saving_percent":
                    12

            })

        return self.recommendations

    # =====================================================
    # GENERAL RECOMMENDATIONS
    # =====================================================

    def general_recommendations(self):
        """
        Add generic energy-saving tips.
        """

        logger.info(
            "Adding general recommendations..."
        )

        tips = [

            "Replace incandescent bulbs with LED lighting.",

            "Turn off appliances when they are not in use.",

            "Use energy-efficient appliances whenever possible.",

            "Run washing machines and dishwashers during off-peak hours.",

            "Service HVAC equipment regularly for better efficiency."

        ]

        for tip in tips:

            self.recommendations.append({

                "category":
                    "General",

                "priority":
                    "Low",

                "recommendation":
                    tip,

                "estimated_saving_percent":
                    2

            })

        return self.recommendations
    
        # =====================================================
    # ESTIMATE SAVINGS
    # =====================================================

    def estimate_savings(self):
        """
        Estimate possible energy savings.
        """

        logger.info(
            "Estimating energy savings..."
        )

        saving_percent = sum(

            recommendation.get(
                "estimated_saving_percent", 0
            )

            for recommendation
            in self.recommendations

        )

        average_daily = self._safe_float(
            self.usage.get("consumption", {}).get("average_daily_energy_kwh")
        )

        from services.savings_calculator import SavingsCalculator
        return SavingsCalculator.calculate_savings(saving_percent, average_daily)

    # =====================================================
    # CO2 REDUCTION
    # =====================================================

    def estimate_co2_reduction(self):
        """
        Estimate yearly and monthly CO₂ reduction.
        """

        logger.info(
            "Estimating CO₂ reduction..."
        )

        savings = self.estimate_savings()
        yearly_saving_kwh = savings["yearly_saving_kwh"]

        from services.savings_calculator import SavingsCalculator
        return SavingsCalculator.calculate_co2_reduction(yearly_saving_kwh)

    # =====================================================
    # GENERATE REPORT
    # =====================================================

    def generate_report(self):
        """
        Generate recommendation report.
        """

        logger.info("=" * 60)
        logger.info(
            "Generating Recommendation Report"
        )
        logger.info("=" * 60)

        report = {

            "recommendations":
                self.recommendations,

            "savings":
                self.estimate_savings(),

            "co2":
                self.estimate_co2_reduction()

        }

        logger.info(
            "Recommendation report generated."
        )

        return report

    # =====================================================
    # COMPLETE PIPELINE
    # =====================================================

    def save_recommendations_to_db(self):
        """Save recommendations into SQLite recommendations table."""
        if not self.recommendations or self.dataset_id is None:
            return
        logger.info(f"Saving recommendations to database for dataset {self.dataset_id}...")
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM recommendations WHERE dataset_id = ?", (self.dataset_id,))
            conn.commit()
            
            for rec in self.recommendations:
                cursor.execute(
                    """
                    INSERT INTO recommendations (dataset_id, category, priority, recommendation, estimated_saving_percent)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        self.dataset_id,
                        rec["category"],
                        rec["priority"],
                        rec["recommendation"],
                        float(rec["estimated_saving_percent"])
                    )
                )
            conn.commit()
            logger.info("Recommendations saved to database successfully.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save recommendations to database: {e}")
        finally:
            conn.close()

    def run_pipeline(self):
        """
        Execute complete recommendation pipeline.
        """

        logger.info("=" * 60)
        logger.info(
            "Starting Recommendation Engine"
        )
        logger.info("=" * 60)

        self.peak_hour_recommendations()

        self.weekend_recommendations()

        self.forecast_recommendations()

        self.anomaly_recommendations()

        self.general_recommendations()

        report = self.generate_report()

        self.save_recommendations_to_db()

        logger.info("=" * 60)
        logger.info(
            "Recommendation Engine Completed"
        )
        logger.info("=" * 60)

        return report


# =====================================================
# STANDALONE EXECUTION
# =====================================================

if __name__ == "__main__":

    print(
        "Recommendation Engine module loaded successfully."
    )