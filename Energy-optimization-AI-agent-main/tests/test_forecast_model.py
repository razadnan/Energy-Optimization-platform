"""
Test Forecast Model
Energy Optimization Agent
"""

from models.forecasting import ForecastingModel


def test_forecast_report_structure(forecast_report):
    report = forecast_report

    assert "summary" in report
    assert "statistics" in report
    assert "evaluation" in report
    assert "forecast" in report


def test_forecast_evaluation_metrics(forecast_report):
    evaluation = forecast_report["evaluation"]

    assert evaluation["model_name"] == "Facebook Prophet"
    assert evaluation["status"] == "Model Trained and Evaluated Successfully"
    assert "mape" in evaluation
    assert "rmse" in evaluation
    assert evaluation["mape"] >= 0
    assert evaluation["rmse"] >= 0


def test_forecast_prediction_rows(forecast_report):
    forecast_rows = forecast_report["forecast"]

    # Forecast rows are serialized as a list of records via convert_numpy_types
    assert len(forecast_rows) == 30

    first_row = forecast_rows[0]
    assert "Date" in first_row
    assert "Predicted_Energy_kWh" in first_row


def test_forecasting_model_class_importable():
    # Regression check: the class must be named ForecastingModel
    model = ForecastingModel()
    assert model is not None


def test_forecast_model_fallback_with_single_day():
    import pandas as pd
    # Create mock dataframe with only 1 unique day of data
    datetime_range = pd.date_range(start="2026-07-20 00:00:00", periods=5, freq="h")
    mock_df = pd.DataFrame({
        "Datetime": datetime_range,
        "Global_active_power": [1.0, 1.2, 1.5, 1.1, 1.3],
        "Global_reactive_power": [0.1, 0.1, 0.2, 0.1, 0.1],
        "Voltage": [230.0, 231.0, 229.0, 230.0, 230.5],
        "Global_intensity": [4.0, 5.0, 6.0, 4.5, 5.2],
        "Sub_metering_1": [0.0, 0.0, 0.0, 0.0, 0.0],
        "Sub_metering_2": [0.0, 0.0, 0.0, 0.0, 0.0],
        "Sub_metering_3": [0.0, 0.0, 0.0, 0.0, 0.0]
    })
    
    model = ForecastingModel()
    model.df = mock_df
    
    # Run the pipeline steps
    model.prepare_training_data()
    assert model.use_baseline is True
    
    model.build_model()
    model.train_model()
    
    report = model.generate_forecast_report()
    
    # Assert correctness of baseline fallback output structure and values
    assert "summary" in report
    assert "statistics" in report
    assert "evaluation" in report
    assert "forecast" in report
    
    evaluation = report["evaluation"]
    assert evaluation["model_name"] == "Facebook Prophet"
    assert evaluation["status"] == "Model Trained and Evaluated Successfully"
    assert evaluation["mape"] == 0.0
    assert evaluation["rmse"] == 0.0
    
    forecast_rows = report["forecast"]
    assert len(forecast_rows) == 30
    assert "Date" in forecast_rows.columns
    assert "Predicted_Energy_kWh" in forecast_rows.columns
    assert (forecast_rows["Predicted_Energy_kWh"] > 0).all()

