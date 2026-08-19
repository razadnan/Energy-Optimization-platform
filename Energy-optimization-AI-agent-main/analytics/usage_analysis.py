"""
=========================================================
Usage Pattern Analytics
Energy Optimization Agent
=========================================================

This module performs analytical calculations on the
processed household energy consumption dataset.

Author : Adnan Raza
Project: Energy Optimization Agent
=========================================================
"""

import pandas as pd

from backend.config import config
from backend.database import DatabaseManager
from services.logger import setup_logger


logger = setup_logger("UsageAnalysis")


class UsageAnalyzer:
    """
    Performs analytical computations on the processed
    energy consumption dataset.

    The analyzer serves as the central analytics engine
    used by multiple AI agents.
    """

    def __init__(self, dataset_id: int = None):
        """
        Initialize analyzer.
        """
        self.dataset_id = dataset_id
        self.file_path = (
            config.PROCESSED_DATA_DIR
            / "processed_energy_data.csv"
        )
        self.df = self.load_processed_data()

    # =====================================================
    # DATA LOADING
    # =====================================================

    def load_processed_data(self):
        """
        Load processed dataset from database.
        """
        logger.info(f"Loading processed dataset from database for dataset_id {self.dataset_id}...")
        df = DatabaseManager.get_data(self.dataset_id)
        logger.info(
            f"Loaded {len(df):,} records successfully."
        )
        return df

    # =====================================================
    # DATASET SUMMARY
    # =====================================================

    def dataset_summary(self):
        """
        Generate overall dataset summary.
        """

        logger.info("Generating dataset summary...")

        summary = {

            "total_records":
                len(self.df),

            "total_columns":
                len(self.df.columns),

            "start_date":
                self.df["Datetime"].min(),

            "end_date":
                self.df["Datetime"].max(),

            "time_span_days":
                (
                    self.df["Datetime"].max()
                    -
                    self.df["Datetime"].min()
                ).days,

            "missing_values":
                int(
                    self.df
                    .isnull()
                    .sum()
                    .sum()
                ),

            "duplicate_rows":
                int(
                    self.df
                    .duplicated()
                    .sum()
                )

        }

        return summary

    # =====================================================
    # DATA QUALITY
    # =====================================================

    def data_quality(self):
        """
        Evaluate processed dataset quality.
        """

        logger.info("Evaluating dataset quality...")

        total_cells = (
            self.df.shape[0]
            *
            self.df.shape[1]
        )

        missing = (
            self.df
            .isnull()
            .sum()
            .sum()
        )

        completeness = round(

            (
                (
                    total_cells
                    -
                    missing
                )
                /
                total_cells
            )
            * 100,

            2

        )

        quality = {

            "rows":
                self.df.shape[0],

            "columns":
                self.df.shape[1],

            "missing_values":
                int(missing),

            "duplicate_rows":
                int(
                    self.df
                    .duplicated()
                    .sum()
                ),

            "data_completeness_percent":
                completeness

        }

        return quality
        # =====================================================
    # CONSUMPTION ANALYSIS
    # =====================================================

    def consumption_analysis(self):
        """
        Calculate energy consumption metrics.
        """

        logger.info("Calculating consumption metrics...")

        # Convert minute-level power (kW) to energy (kWh)
        total_energy = round(
            self.df["Global_active_power"].sum() / 60,
            2
        )

        average_power = round(
            self.df["Global_active_power"].mean(),
            3
        )

        daily_energy = (
            self.df
            .groupby(
                self.df["Datetime"].dt.date
            )["Global_active_power"]
            .sum()
            / 60
        )

        monthly_energy = (
            self.df
            .groupby(
                self.df["Datetime"].dt.to_period("M")
            )["Global_active_power"]
            .sum()
            / 60
        )

        hourly_energy = (
            self.df
            .groupby("Hour")["Global_active_power"]
            .mean()
        )

        consumption = {

            "total_energy_kwh":
                total_energy,

            "average_power_kw":
                average_power,

            "average_daily_energy_kwh":
                round(
                    daily_energy.mean(),
                    2
                ),

            "average_monthly_energy_kwh":
                round(
                    monthly_energy.mean(),
                    2
                ),

            "maximum_daily_energy_kwh":
                round(
                    daily_energy.max(),
                    2
                ),

            "minimum_daily_energy_kwh":
                round(
                    daily_energy.min(),
                    2
                ),

            "maximum_hourly_average_kw":
                round(
                    hourly_energy.max(),
                    3
                ),

            "minimum_hourly_average_kw":
                round(
                    hourly_energy.min(),
                    3
                )

        }

        return consumption

    # =====================================================
    # PEAK USAGE ANALYSIS
    # =====================================================

    def peak_usage_analysis(self):
        """
        Analyze energy usage peaks.
        """

        logger.info("Analyzing peak usage patterns...")

        hourly_usage = (
            self.df
            .groupby("Hour")["Global_active_power"]
            .mean()
        )

        weekday_usage = (
            self.df
            .groupby("Weekday")["Global_active_power"]
            .mean()
        )

        monthly_usage = (
            self.df
            .groupby("Month")["Global_active_power"]
            .mean()
        )

        analysis = {

            "peak_hour":
                int(
                    hourly_usage.idxmax()
                ),

            "lowest_hour":
                int(
                    hourly_usage.idxmin()
                ),

            "peak_hour_average_kw":
                round(
                    hourly_usage.max(),
                    3
                ),

            "lowest_hour_average_kw":
                round(
                    hourly_usage.min(),
                    3
                ),

            "peak_weekday":
                weekday_usage.idxmax(),

            "lowest_weekday":
                weekday_usage.idxmin(),

            "peak_month":
                int(
                    monthly_usage.idxmax()
                ),

            "lowest_month":
                int(
                    monthly_usage.idxmin()
                )

        }

        return analysis
    
        # =====================================================
    # TREND ANALYSIS
    # =====================================================

    def trend_analysis(self):
        """
        Analyze hourly, daily and monthly energy trends.
        """

        logger.info("Analyzing energy consumption trends...")

        hourly_trend = (
            self.df
            .groupby("Hour")["Global_active_power"]
            .mean()
            .round(3)
            .to_dict()
        )

        daily_trend = (
            self.df
            .groupby(
                self.df["Datetime"].dt.date
            )["Global_active_power"]
            .sum()
            .div(60)
            .round(2)
            .tail(30)
            .to_dict()
        )

        monthly_trend = (
            self.df
            .groupby(
                self.df["Datetime"].dt.to_period("M")
            )["Global_active_power"]
            .sum()
            .div(60)
            .round(2)
        )

        monthly_trend = {
            str(k): v
            for k, v in monthly_trend.items()
        }

        return {

            "hourly_trend":
                hourly_trend,

            "daily_trend":
                daily_trend,

            "monthly_trend":
                monthly_trend

        }

    # =====================================================
    # WEEKDAY VS WEEKEND ANALYSIS
    # =====================================================

    def weekday_weekend_analysis(self):
        """
        Compare weekday and weekend consumption.
        """

        logger.info(
            "Analyzing weekday/weekend usage..."
        )

        weekday = self.df[
            self.df["Is_Weekend"] == 0
        ]

        weekend = self.df[
            self.df["Is_Weekend"] == 1
        ]

        weekday_avg = round(

            weekday[
                "Global_active_power"
            ].mean(),

            3

        )

        weekend_avg = round(

            weekend[
                "Global_active_power"
            ].mean(),

            3

        )

        comparison = {

            "weekday_average_kw":
                weekday_avg,

            "weekend_average_kw":
                weekend_avg,

            "difference_kw":
                round(
                    weekend_avg - weekday_avg,
                    3
                )

        }

        return comparison

    # =====================================================
    # SUB-METER ANALYSIS
    # =====================================================

    def submeter_analysis(self):
        """
        Analyze appliance sub-meter usage.
        """

        logger.info(
            "Analyzing appliance sub-meters..."
        )

        sub1 = round(

            self.df[
                "Sub_metering_1"
            ].sum(),

            2

        )

        sub2 = round(

            self.df[
                "Sub_metering_2"
            ].sum(),

            2

        )

        sub3 = round(

            self.df[
                "Sub_metering_3"
            ].sum(),

            2

        )

        total = round(

            sub1 + sub2 + sub3,

            2

        )

        return {

            "kitchen_wh":
                sub1,

            "laundry_wh":
                sub2,

            "water_heater_hvac_wh":
                sub3,

            "total_submeter_wh":
                total

        }
        # =====================================================
    # COMPLETE ANALYTICS REPORT
    # =====================================================

    def generate_report(self):
        """
        Generate the complete analytics report.

        This method acts as the single entry point for all
        analytics required by the Usage Agent.
        """

        logger.info("=" * 60)
        logger.info("Generating Complete Usage Analytics Report")
        logger.info("=" * 60)

        report = {

            "summary":
                self.dataset_summary(),

            "quality":
                self.data_quality(),

            "consumption":
                self.consumption_analysis(),

            "peak_usage":
                self.peak_usage_analysis(),

            "trends":
                self.trend_analysis(),

            "weekday_weekend":
                self.weekday_weekend_analysis(),

            "submeter":
                self.submeter_analysis()

        }

        logger.info("=" * 60)
        logger.info("Usage Analytics Report Generated Successfully")
        logger.info("=" * 60)

        return report


# =========================================================
# END OF FILE
# =========================================================