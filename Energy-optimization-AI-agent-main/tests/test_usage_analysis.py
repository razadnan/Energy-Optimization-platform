"""
Test Usage Analysis
Energy Optimization Agent
"""


def test_usage_report_structure(usage_report):
    report = usage_report

    assert "summary" in report
    assert "quality" in report
    assert "consumption" in report
    assert "peak_usage" in report
    assert "weekday_weekend" in report
    assert "submeter" in report
    assert "trends" in report


def test_usage_report_values(usage_report):
    report = usage_report

    assert report["summary"]["total_records"] > 0
    assert report["consumption"]["average_daily_energy_kwh"] >= 0
    assert report["quality"]["data_completeness_percent"] >= 0

    assert 0 <= report["peak_usage"]["peak_hour"] <= 23

    assert len(report["trends"]["hourly_trend"]) > 0
    assert len(report["trends"]["daily_trend"]) > 0
    assert len(report["trends"]["monthly_trend"]) > 0
