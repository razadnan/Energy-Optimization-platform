import streamlit as st
import pandas as pd
from components.header import render_header
from components.sidebar import render_sidebar
from components.theme import configure_page
from dashboard.utils.data_loader import load_recommendation_data
from components.floating_ai import floating_ai
from backend.config import config

configure_page()
render_sidebar()
render_header()

from dashboard.utils.data_loader import check_active_dataset_status
check_active_dataset_status()

st.title("💡 Optimization Recommendations")

active_id = st.session_state.get("active_dataset_id")
if not active_id:
    st.warning("⚠️ No active dataset found. Please upload a dataset on the Overview page to unlock recommendations!")
    st.stop()

with st.spinner("Generating cost-saving recommendations..."):
    recs_data = load_recommendation_data(active_id)

if recs_data:
    # 1. KPIs
    col1, col2, col3 = st.columns(3)
    savings = recs_data["savings"]
    co2 = recs_data["co2"]
    
    with col1:
        st.metric("Potential Monthly Savings", f"₹{savings['estimated_monthly_savings_rupees']:.2f}")
    with col2:
        st.metric("Estimated Monthly CO₂ Reduction", f"{co2['estimated_monthly_co2_reduction_kg']:.2f} kg")
    with col3:
        st.metric("Actionable Insights", f"{len(recs_data['recommendations'])} items")

    st.write("")

    # 2. Recommendations List
    st.subheader("📋 Core Action Plan")
    recs_list = recs_data["recommendations"]
    
    for rec in recs_list:
        priority = rec["priority"]
        badge_color = "red" if priority == "High" else "orange" if priority == "Medium" else "blue"
        st.markdown(
            f"""
            <div style="padding:15px; border-radius:8px; border-left: 5px solid {badge_color}; background-color:#F9FAFB; margin-bottom:12px;">
                <span style="font-weight:bold; color:#374151;">[{rec['category']}]</span>
                <span style="float:right; font-size:0.85em; font-weight:bold; color:white; background-color:{badge_color}; padding:2px 8px; border-radius:4px;">{priority} Priority</span>
                <p style="margin-top:8px; color:#4B5563;">{rec['recommendation']}</p>
                <span style="font-size:0.9em; color:#16A34A; font-weight:bold;">⚡ Est. Consumption Reduction: {rec['estimated_saving_percent']}%</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")
    st.divider()
    st.write("")

    # 3. Interactive What-If Simulator
    st.subheader("🎛️ Interactive 'What-If' Savings Simulator")
    st.markdown("Adjust parameters below to see how shifts in appliance behavior instantly reduce your bills and emissions.")

    left, right = st.columns([1, 1.2])
    
    with left:
        st.info("⚙️ Simulation Settings")
        ac_reduction = st.slider("Reduce AC/Heating runtime (Hours/Day)", 0, 12, 2)
        led_replace = st.slider("Replace incandescent bulbs with LEDs", 0, 20, 5)
        load_shift = st.slider("Shift appliance usage to Off-Peak (Hours/Day)", 0, 100, 30, format="%d%%")
        
    with right:
        # Math calculations
        # 1. AC consumes roughly 1.5 kW. 1 hour/day = 1.5 kWh/day.
        ac_kwh_saved = ac_reduction * 1.5 * 30
        
        # 2. Bulbs: 60W bulb replaced by 9W LED bulb saves 51W. Running 5 hours/day:
        led_kwh_saved = led_replace * (51 / 1000) * 5 * 30
        
        # 3. Load shift: shifting 30% of average daily consumption from peak to off-peak
        # Let's say off-peak has a net virtual benefit equivalent to 15% efficiency savings
        avg_daily = recs_data["savings"]["monthly_saving_kwh"] / 0.3 # base daily
        shifted_kwh_saved = (load_shift / 100) * avg_daily * 0.15
        
        total_kwh_saved = ac_kwh_saved + led_kwh_saved + shifted_kwh_saved
        monthly_cost_saved = total_kwh_saved * config.ELECTRICITY_RATE
        monthly_co2_saved = total_kwh_saved * config.CO2_PER_KWH
        
        st.success("💰 Estimated Simulation Results")
        
        st.markdown(
            f"""
            <div style="padding: 20px; border-radius: 8px; background-color: #ECFDF5; border: 1px solid #10B981; text-align: center;">
                <h3 style="margin: 0; color: #065F46;">Total Monthly Savings</h3>
                <h1 style="margin: 10px 0; color: #059669; font-size: 3em;">₹{monthly_cost_saved:,.2f}</h1>
                <p style="margin: 5px 0; color: #047857; font-weight: bold;">⚡ Energy Saved: {total_kwh_saved:.1f} kWh / month</p>
                <p style="margin: 5px 0; color: #047857; font-weight: bold;">🌱 Carbon Reduction: {monthly_co2_saved:.1f} kg CO₂ / month</p>
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    st.warning("Unable to load optimization recommendations.")

floating_ai()