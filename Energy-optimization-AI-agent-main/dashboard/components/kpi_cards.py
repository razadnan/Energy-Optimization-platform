import streamlit as st
from dashboard.utils.data_loader import load_usage_data, load_recommendation_data


def render_kpi_cards():
    active_id = st.session_state.get("active_dataset_id")
    usage_data = load_usage_data(active_id) if active_id else None
    recs_data = load_recommendation_data(active_id) if active_id else None

    col1, col2, col3, col4 = st.columns(4)

    # 1. Energy Usage
    if usage_data:
        total_energy = usage_data["consumption"]["total_energy_kwh"]
        energy_val = f"{total_energy:,.0f} kWh"
    else:
        energy_val = "--"

    # 2. Monthly Savings
    if recs_data:
        savings = recs_data["savings"]["estimated_monthly_savings_rupees"]
        savings_val = f"₹{savings:,.0f}"
    else:
        savings_val = "--"

    # 3. CO2 Reduction
    if recs_data:
        co2_val = f"{recs_data['co2']['estimated_monthly_co2_reduction_kg']:.1f} kg"
    else:
        co2_val = "--"

    with col1:
        st.metric(
            "⚡ Total Consumption",
            energy_val
        )

    with col2:
        st.metric(
            "💰 Monthly Savings",
            savings_val
        )

    with col3:
        st.metric(
            "🌱 CO₂ Reduction",
            co2_val
        )

    with col4:
        st.metric(
            "🤖 AI Pipeline",
            "Online",
            "5 Agents"
        )