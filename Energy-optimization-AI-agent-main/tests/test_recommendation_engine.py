"""
Test Recommendation Engine
Energy Optimization Agent
"""


def test_recommendation_report_structure(recommendation_report):
    report = recommendation_report

    assert "recommendations" in report
    assert "savings" in report
    assert "co2" in report


def test_recommendations_list(recommendation_report):
    recs = recommendation_report["recommendations"]

    assert isinstance(recs, list)
    assert len(recs) > 0

    for rec in recs:
        assert "category" in rec
        assert "priority" in rec
        assert "recommendation" in rec
        assert "estimated_saving_percent" in rec
        assert rec["priority"] in {"High", "Medium", "Low"}


def test_savings_and_co2(recommendation_report):
    savings = recommendation_report["savings"]
    co2 = recommendation_report["co2"]

    assert savings["estimated_monthly_savings_rupees"] >= 0
    assert savings["monthly_saving_kwh"] >= 0
    assert co2["estimated_monthly_co2_reduction_kg"] >= 0
