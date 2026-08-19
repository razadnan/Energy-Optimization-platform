class ReportGenerator:
    """
    Generates structured summaries and markdown reports combining
    usage pattern analysis, forecasting, anomalies, and recommendations.
    """

    def __init__(self, data: dict):
        self.usage = data.get("usage", {})
        self.forecast = data.get("forecast", {})
        self.anomaly = data.get("anomaly", {})
        self.recommendation = data.get("recommendation", {})
        self.insight = data.get("insight", {})

    def generate_markdown(self) -> str:
        """
        Create a comprehensive markdown summary report.
        """
        def clean_val(v, default=0.0):
            if v is None:
                return default
            try:
                import math
                f = float(v)
                return default if math.isnan(f) or math.isinf(f) else f
            except Exception:
                return default

        # Usage Stats
        avg_usage = clean_val(
            self.usage.get("consumption", {}).get("average_daily_energy_kwh", 
            self.usage.get("consumption", {}).get("average_daily_kwh"))
        )
        peak_hour = self.usage.get("peak_usage", {}).get("peak_hour", "N/A")
        if peak_hour is not None:
            try:
                import math
                if isinstance(peak_hour, float) and math.isnan(peak_hour):
                    peak_hour = "N/A"
            except Exception:
                pass
        peak_kw = clean_val(self.usage.get("peak_usage", {}).get("peak_hour_average_kw", 0.0))

        # Forecast Stats
        forecast_eval = self.forecast.get("evaluation", {})
        mape = forecast_eval.get("mape", "N/A")
        rmse = forecast_eval.get("rmse", "N/A")

        # Anomaly Stats
        anomaly_stats = self.anomaly.get("statistics", {})
        anomaly_count = anomaly_stats.get("anomaly_records", 0)
        try:
            import math
            if anomaly_count is None or (isinstance(anomaly_count, float) and math.isnan(anomaly_count)):
                anomaly_count = 0
            else:
                anomaly_count = int(anomaly_count)
        except Exception:
            anomaly_count = 0
            
        anomaly_pct = clean_val(anomaly_stats.get("anomaly_percentage", 0.0))
        critical_count = anomaly_stats.get("critical_anomalies", 0)
        try:
            import math
            if critical_count is None or (isinstance(critical_count, float) and math.isnan(critical_count)):
                critical_count = 0
            else:
                critical_count = int(critical_count)
        except Exception:
            critical_count = 0

        # Recommendations
        recs = self.recommendation.get("recommendations", [])
        savings = self.recommendation.get("savings", {})
        monthly_saving = clean_val(savings.get("estimated_monthly_savings_rupees", 0.0))
        co2_reduction = clean_val(self.recommendation.get("co2", {}).get("estimated_monthly_co2_reduction_kg", 0.0))

        # Weekday/weekend and submeter formatting values
        weekday_avg = clean_val(self.usage.get('weekday_weekend', {}).get('weekday_average_kw', 0.0))
        weekend_avg = clean_val(self.usage.get('weekday_weekend', {}).get('weekend_average_kw', 0.0))
        kitchen_wh = clean_val(self.usage.get('submeter', {}).get('kitchen_wh', 0.0))
        laundry_wh = clean_val(self.usage.get('submeter', {}).get('laundry_wh', 0.0))
        hvac_wh = clean_val(self.usage.get('submeter', {}).get('water_heater_hvac_wh', 0.0))

        # AI Insight (reasoning layer) - only rendered if InsightAgent ran
        insight_section = ""
        if self.insight:
            alert_level = self.insight.get("alert_level", "Normal")
            primary_concern = self.insight.get("primary_concern", "")
            reasoning = self.insight.get("reasoning", "")
            exec_summary = self.insight.get("executive_summary", "")
            source = self.insight.get("source", "llm")
            source_note = (
                "AI-generated judgment"
                if source == "llm"
                else "deterministic fallback - LLM unavailable"
            )
            insight_section = f"""
## 1a. AI Insight Agent — Reasoning Layer
**Alert Level:** {alert_level}  ({source_note})

**Primary Concern:** {primary_concern}

**Reasoning:** {reasoning}

**Executive Summary (AI-generated):** {exec_summary}

---
"""

        markdown = f"""# Energy Intelligence Audit Report

## 1. Executive Summary
This report presents an automated analysis of home energy consumption patterns, forecast projections, anomaly detections, and cost optimization recommendations.

* **Average Daily Consumption:** {avg_usage:.2f} kWh
* **Peak Demand Hour:** {peak_hour}:00 ({peak_kw:.2f} kW avg)
* **Active Recommendations:** {len(recs)}
* **Potential Monthly Savings:** ₹{monthly_saving:.2f}
* **Estimated CO₂ Reduction:** {co2_reduction:.2f} kg/month

---
{insight_section}
## 2. Energy Usage Patterns
The analyzer evaluated historical minute-level energy readings.
* **Weekday vs Weekend:** Weekday average is {weekday_avg:.2f} kW vs Weekend average {weekend_avg:.2f} kW.
* **Sub-metering Distribution:**
  * Kitchen: {kitchen_wh:,.2f} Wh
  * Laundry: {laundry_wh:,.2f} Wh
  * HVAC & Water Heater: {hvac_wh:,.2f} Wh

---

## 3. Predictive Forecast (Facebook Prophet)
Future projections spanning the next 30 days have been generated:
* **Model Confidence Metrics:** MAPE = {mape}%, RMSE = {rmse}
* **Expected Trend Direction:** {self.forecast.get('summary', {}).get('trend_direction', 'Stable')}

---

## 4. Anomaly Detection (Isolation Forest)
We scanned all records to identify abnormal spikes or drops in consumption:
* **Anomalies Found:** {anomaly_count:,} ({anomaly_pct}% of total records)
* **Critical-severity Spikes:** {critical_count} events

---

## 5. Tailored Recommendations
The system generated the following optimization tasks:
"""
        for i, rec in enumerate(recs, 1):
            markdown += f"{i}. **[{rec.get('priority', 'Medium')}] {rec.get('category', 'General')}**: {rec.get('recommendation')} (Est. Saving: {rec.get('estimated_saving_percent', 0)}%)\n"

        return markdown

    def generate_report(self) -> dict:
        """
        Generate complete reporting structure.
        """
        return {
            "summary_markdown": self.generate_markdown(),
            "status": "Report generated successfully",
            "alert_level": self.insight.get("alert_level", "Normal") if self.insight else "Normal"
        }
