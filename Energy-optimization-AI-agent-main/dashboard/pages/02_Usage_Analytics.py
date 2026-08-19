import streamlit as st
import plotly.express as px
import pandas as pd
from components.header import render_header
from components.sidebar import render_sidebar
from components.theme import configure_page
from dashboard.utils.data_loader import load_usage_data
from components.floating_ai import floating_ai

configure_page()
render_sidebar()
render_header()

from dashboard.utils.data_loader import check_active_dataset_status
check_active_dataset_status()

st.title("📈 Energy Usage Analytics")

active_id = st.session_state.get("active_dataset_id")
if not active_id:
    st.warning("⚠️ No active dataset found. Please upload a dataset on the Overview page to unlock analytics!")
    st.stop()

with st.spinner("Analyzing usage patterns from dataset..."):
    usage_data = load_usage_data(active_id)

if usage_data:
    # 1. KPIs
    col1, col2, col3 = st.columns(3)
    avg_daily = usage_data["consumption"]["average_daily_energy_kwh"]
    total_energy = usage_data["consumption"]["total_energy_kwh"]
    peak_hour = usage_data["peak_usage"]["peak_hour"]
    peak_kw = usage_data["peak_usage"]["peak_hour_average_kw"]
    
    with col1:
        st.metric("Average Daily Energy", f"{avg_daily:.2f} kWh")
    with col2:
        st.metric("Total Active Consumption", f"{total_energy:,.2f} kWh")
    with col3:
        st.metric("Peak Hour Peak load", f"{peak_hour}:00 ({peak_kw:.2f} kW)")

    st.write("")

    # 2. Daily Consumption Over Time
    st.subheader("📅 Daily Energy Consumption (Fitted/Historical)")
    daily_trend = usage_data["trends"]["daily_trend"]
    df_daily = pd.DataFrame([
        {"Date": k, "Energy_kWh": v} for k, v in daily_trend.items()
    ])
    df_daily["Date"] = pd.to_datetime(df_daily["Date"])
    df_daily = df_daily.sort_values("Date")
    
    fig_daily = px.line(
        df_daily,
        x="Date",
        y="Energy_kWh",
        title="Daily Energy Consumption Over Time",
        color_discrete_sequence=["#15803D"]
    )
    fig_daily.update_layout(template="plotly_white", height=400)
    st.plotly_chart(fig_daily, width="stretch")

    # 3. Two columns for Submeter distribution and Weekday/weekend
    left, right = st.columns(2)
    
    with left:
        st.subheader("🔌 Appliance Category Breakdown")
        submeter = usage_data["submeter"]
        submeter_df = pd.DataFrame({
            "Appliance Category": ["Kitchen", "Laundry Room", "HVAC / Water Heater"],
            "Consumption (Wh)": [submeter["kitchen_wh"], submeter["laundry_wh"], submeter["water_heater_hvac_wh"]]
        })
        fig_pie = px.pie(
            submeter_df,
            values="Consumption (Wh)",
            names="Appliance Category",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Greens_r
        )
        fig_pie.update_layout(template="plotly_white", height=350)
        st.plotly_chart(fig_pie, width="stretch")
        
    with right:
        st.subheader("📅 Weekday vs. Weekend Analysis")
        ww = usage_data["weekday_weekend"]
        ww_df = pd.DataFrame({
            "Day Type": ["Weekdays", "Weekends"],
            "Average Power (kW)": [ww["weekday_average_kw"], ww["weekend_average_kw"]]
        })
        fig_bar = px.bar(
            ww_df,
            x="Day Type",
            y="Average Power (kW)",
            color="Day Type",
            color_discrete_sequence=["#16A34A", "#86EFAC"]
        )
        fig_bar.update_layout(template="plotly_white", height=350, showlegend=False)
        st.plotly_chart(fig_bar, width="stretch")

    # 4. Hourly consumption trend
    st.subheader("⏰ Average Hourly Profile (Peak Analysis)")
    hourly_trend = usage_data["trends"]["hourly_trend"]
    df_hourly = pd.DataFrame([
        {"Hour": int(k), "Average_kW": v} for k, v in hourly_trend.items()
    ])
    df_hourly = df_hourly.sort_values("Hour")
    fig_hourly = px.area(
        df_hourly,
        x="Hour",
        y="Average_kW",
        title="Hourly Average Load (kW) Profile",
        color_discrete_sequence=["#22C55E"]
    )
    fig_hourly.update_layout(template="plotly_white", height=350)
    st.plotly_chart(fig_hourly, width="stretch")

else:
    st.warning("Unable to load usage data. Please verify dataset is preprocessed.")

floating_ai()