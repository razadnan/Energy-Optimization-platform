import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from components.header import render_header
from components.sidebar import render_sidebar
from components.theme import configure_page
from dashboard.utils.data_loader import load_forecast_data
from components.floating_ai import floating_ai
configure_page()
render_sidebar()
render_header()

from dashboard.utils.data_loader import check_active_dataset_status
check_active_dataset_status()

st.title("🔮 Consumption Forecasting")

active_id = st.session_state.get("active_dataset_id")
if not active_id:
    st.warning("⚠️ No active dataset found. Please upload a dataset on the Overview page to unlock forecasting!")
    st.stop()

with st.spinner("Generating prediction projections using Facebook Prophet..."):
    forecast_data = load_forecast_data(active_id)

if forecast_data:
    # 1. KPIs
    col1, col2, col3 = st.columns(3)
    eval_metrics = forecast_data["evaluation"]
    stats = forecast_data["statistics"]
    
    with col1:
        st.metric("Model Engine", eval_metrics["model_name"])
    with col2:
        st.metric("Model MAPE / RMSE", f"{eval_metrics['mape']:.2f}% / {eval_metrics['rmse']:.2f} kWh")
    with col3:
        st.metric("Avg Predicted Energy", f"{stats['average_prediction']:.2f} kWh")

    st.write("")

    # 2. Plot Forecast
    st.subheader("🔮 30-Day Projections (Forecast)")
    df_forecast = pd.DataFrame(forecast_data["forecast"])
    df_forecast["Date"] = pd.to_datetime(df_forecast["Date"])
    df_forecast = df_forecast.sort_values("Date")
    
    fig = go.Figure()
    
    # Lower bound
    fig.add_trace(go.Scatter(
        x=df_forecast["Date"],
        y=df_forecast["Lower_Bound"],
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        name="Lower Bound"
    ))
    
    # Upper bound with fill to lower bound
    fig.add_trace(go.Scatter(
        x=df_forecast["Date"],
        y=df_forecast["Upper_Bound"],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(34, 197, 94, 0.15)',
        line=dict(width=0),
        name="Confidence Band (Uncertainty)",
        showlegend=True
    ))
    
    # Core predicted line
    fig.add_trace(go.Scatter(
        x=df_forecast["Date"],
        y=df_forecast["Predicted_Energy_kWh"],
        mode='lines+markers',
        line=dict(color='#16A34A', width=2.5),
        name="Predicted Energy (kWh)",
        showlegend=True
    ))
    
    fig.update_layout(
        template="plotly_white",
        height=450,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, width="stretch")

    # 3. Forecast Table View
    st.subheader("📋 Forecast Data Table")
    display_df = df_forecast.rename(columns={
        "Date": "Date",
        "Predicted_Energy_kWh": "Predicted Energy (kWh)",
        "Lower_Bound": "Lower Confidence (kWh)",
        "Upper_Bound": "Upper Confidence (kWh)"
    })
    st.dataframe(display_df, width="stretch", hide_index=True)

else:
    st.warning("Unable to load forecasting data.")
floating_ai()