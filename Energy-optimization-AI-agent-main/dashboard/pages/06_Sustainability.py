import streamlit as st
from components.header import render_header
from components.sidebar import render_sidebar
from components.theme import configure_page
from dashboard.utils.data_loader import load_recommendation_data
from components.floating_ai import floating_ai

configure_page()
render_sidebar()
render_header()

from dashboard.utils.data_loader import check_active_dataset_status
check_active_dataset_status()

active_id = st.session_state.get("active_dataset_id")
if not active_id:
    st.warning("⚠️ No active dataset found. Please upload a dataset on the Overview page to unlock sustainability metrics!")
    st.stop()

with st.spinner("Calculating environmental impact metrics..."):
    recs_data = load_recommendation_data(active_id)

if recs_data:
    co2 = recs_data["co2"]
    yearly_co2 = co2["estimated_yearly_co2_reduction_kg"]
    monthly_co2 = co2["estimated_monthly_co2_reduction_kg"]

    # KPIs
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Yearly CO₂ Saved", f"{yearly_co2:,.1f} kg")
    with col2:
        st.metric("Monthly CO₂ Saved", f"{monthly_co2:,.1f} kg")

    st.write("")
    st.subheader("🌲 Equivalent Environmental Offsets")
    
    # Equivalents math
    # 1 mature tree absorbs ~22kg of CO2 per year
    trees_offset = yearly_co2 / 22.0
    
    # 1 typical passenger vehicle emits ~4,600 kg of CO2 per year (~383 kg/month)
    car_days_offset = (yearly_co2 / 4600.0) * 365
    
    # 1 smartphone charge is roughly 0.008 kg of CO2
    phone_charges = yearly_co2 / 0.008

    left, middle, right = st.columns(3)
    
    with left:
        st.markdown(
            f"""
            <div style="padding:20px; border-radius:8px; background-color:#EFF6FF; border:1px solid #3B82F6; text-align:center; min-height:180px;">
                <h2 style="font-size:2.5em; margin:0;">🌲</h2>
                <h3 style="margin:10px 0 5px; color:#1E3A8A;">{trees_offset:.1f}</h3>
                <p style="color:#2563EB; font-size:0.9em; margin:0;">Mature Trees Planted / Year</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with middle:
        st.markdown(
            f"""
            <div style="padding:20px; border-radius:8px; background-color:#ECFDF5; border:1px solid #10B981; text-align:center; min-height:180px;">
                <h2 style="font-size:2.5em; margin:0;">🚗</h2>
                <h3 style="margin:10px 0 5px; color:#065F46;">{car_days_offset:.1f}</h3>
                <p style="color:#059669; font-size:0.9em; margin:0;">Vehicle-Days Taken Off Road</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with right:
        st.markdown(
            f"""
            <div style="padding:20px; border-radius:8px; background-color:#FFFBEB; border:1px solid #F59E0B; text-align:center; min-height:180px;">
                <h2 style="font-size:2.5em; margin:0;">🔌</h2>
                <h3 style="margin:10px 0 5px; color:#78350F;">{phone_charges:,.0f}</h3>
                <p style="color:#D97706; font-size:0.9em; margin:0;">Smartphones Charged</p>
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    st.warning("Unable to load sustainability data.")
floating_ai()