"""
Test Anomaly Detection Model
Energy Optimization Agent
"""


def test_anomaly_report_structure(anomaly_report):
    report = anomaly_report

    assert "statistics" in report
    assert "hourly_analysis" in report
    assert "daily_analysis" in report
    assert "high_risk_records" in report


def test_anomaly_statistics(anomaly_report):
    stats = anomaly_report["statistics"]

    assert stats["total_records"] > 0
    assert stats["anomaly_records"] >= 0
    assert stats["normal_records"] >= 0
    assert stats["anomaly_records"] + stats["normal_records"] == stats["total_records"]
    assert 0 <= stats["anomaly_percentage"] <= 100

    severity_total = (
        stats["critical_anomalies"]
        + stats["high_anomalies"]
        + stats["medium_anomalies"]
    )
    assert severity_total == stats["anomaly_records"]


def test_high_risk_records(anomaly_report):
    high_risk = anomaly_report["high_risk_records"]

    assert len(high_risk) <= 10
    if high_risk:
        record = high_risk[0]
        assert "Datetime" in record
        assert "Anomaly_Score" in record
        assert "Severity" in record
        assert record["Severity"] in {"Critical", "High", "Medium"}
