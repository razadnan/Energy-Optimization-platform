from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# =====================================================
# USAGE SCHEMAS
# =====================================================
class DatasetSummarySchema(BaseModel):
    total_records: int
    total_columns: int
    start_date: str
    end_date: str
    time_span_days: int
    missing_values: int
    duplicate_rows: int

class DataQualitySchema(BaseModel):
    rows: int
    columns: int
    missing_values: int
    duplicate_rows: int
    data_completeness_percent: float

class ConsumptionAnalysisSchema(BaseModel):
    total_energy_kwh: float
    average_power_kw: float
    average_daily_energy_kwh: float
    average_monthly_energy_kwh: float
    maximum_daily_energy_kwh: float
    minimum_daily_energy_kwh: float
    maximum_hourly_average_kw: float
    minimum_hourly_average_kw: float

class PeakUsageSchema(BaseModel):
    peak_hour: int
    lowest_hour: int
    peak_hour_average_kw: float
    lowest_hour_average_kw: float

class TrendAnalysisSchema(BaseModel):
    hourly_trend: Dict[str, float]
    daily_trend: Dict[str, float]
    monthly_trend: Dict[str, float]

class WeekdayWeekendSchema(BaseModel):
    weekday_average_kw: float
    weekend_average_kw: float
    difference_kw: float

class SubmeterSchema(BaseModel):
    kitchen_wh: float
    laundry_wh: float
    water_heater_hvac_wh: float
    total_submeter_wh: float

class UsageReportSchema(BaseModel):
    summary: DatasetSummarySchema
    quality: DataQualitySchema
    consumption: ConsumptionAnalysisSchema
    peak_usage: PeakUsageSchema
    trends: TrendAnalysisSchema
    weekday_weekend: WeekdayWeekendSchema
    submeter: SubmeterSchema

# =====================================================
# FORECAST SCHEMAS
# =====================================================
class ForecastSummarySchema(BaseModel):
    training_samples: int
    training_start: str
    training_end: str
    forecast_days: int
    model: str

class ForecastStatisticsSchema(BaseModel):
    minimum_prediction: float
    maximum_prediction: float
    average_prediction: float
    total_predicted_energy: float

class ForecastEvaluationSchema(BaseModel):
    model_name: str
    training_samples: int
    forecast_days: int
    mape: float
    rmse: float
    status: str

class ForecastPredictionRowSchema(BaseModel):
    Date: str
    Predicted_Energy_kWh: float
    Lower_Bound: float
    Upper_Bound: float

class ForecastReportSchema(BaseModel):
    summary: ForecastSummarySchema
    statistics: ForecastStatisticsSchema
    evaluation: ForecastEvaluationSchema
    forecast: List[ForecastPredictionRowSchema]

# =====================================================
# ANOMALY SCHEMAS
# =====================================================
class AnomalyStatisticsSchema(BaseModel):
    total_records: int
    normal_records: int
    anomaly_records: int
    anomaly_percentage: float
    critical_anomalies: int
    high_anomalies: int
    medium_anomalies: int

class AnomalyRecordSchema(BaseModel):
    Datetime: str
    Global_active_power: float
    Voltage: float
    Global_intensity: float
    Anomaly_Score: float
    Severity: str

class AnomalyReportSchema(BaseModel):
    statistics: AnomalyStatisticsSchema
    hourly_analysis: Dict[str, int]
    daily_analysis: Dict[str, int]
    high_risk_records: List[AnomalyRecordSchema]

# =====================================================
# RECOMMENDATION SCHEMAS
# =====================================================
class RecommendationItemSchema(BaseModel):
    category: str
    priority: str
    recommendation: str
    estimated_saving_percent: float

class SavingsEstimateSchema(BaseModel):
    estimated_saving_percent: float
    daily_saving_kwh: float
    monthly_saving_kwh: float
    yearly_saving_kwh: float
    estimated_daily_savings_rupees: float
    estimated_monthly_savings_rupees: float
    estimated_yearly_savings_rupees: float

class CO2ReductionSchema(BaseModel):
    estimated_yearly_co2_reduction_kg: float
    estimated_monthly_co2_reduction_kg: float

class RecommendationReportSchema(BaseModel):
    recommendations: List[RecommendationItemSchema]
    savings: SavingsEstimateSchema
    co2: CO2ReductionSchema

# =====================================================
# CHAT SCHEMAS (real-time AI assistant)
# =====================================================
class ChatMessageSchema(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequestSchema(BaseModel):
    message: str
    history: List[ChatMessageSchema] = []

class ChatResponseSchema(BaseModel):
    reply: str
    source: str  # "llm" or "fallback"

# =====================================================
# INSIGHT SCHEMAS (AI reasoning layer)
# =====================================================
class InsightReportSchema(BaseModel):
    alert_level: str
    primary_concern: str
    reasoning: str
    executive_summary: str
    source: str  # "llm" or "fallback"

# =====================================================
# REPORT SCHEMAS
# =====================================================
class ReportingResponseSchema(BaseModel):
    summary_markdown: str
    status: str
    alert_level: str = "Normal"
