import streamlit as st
import plotly.express as px
import pandas as pd
from components.header import render_header
from components.sidebar import render_sidebar
from components.theme import configure_page
from dashboard.utils.data_loader import load_anomaly_data
from components.floating_ai import floating_ai

configure_page()
render_sidebar()
render_header()

from dashboard.utils.data_loader import check_active_dataset_status
check_active_dataset_status()

st.title("🚨 Anomaly Detection")

active_id = st.session_state.get("active_dataset_id")
if not active_id:
    st.warning("⚠️ No active dataset found. Please upload a dataset on the Overview page to unlock anomaly detection!")
    st.stop()

with st.spinner("Analyzing anomalies via Isolation Forest..."):
    anomaly_data = load_anomaly_data(active_id)

if anomaly_data:
    # 1. KPIs
    col1, col2, col3, col4 = st.columns(4)
    stats = anomaly_data["statistics"]
    
    with col1:
        st.metric("Contamination Rate", f"{stats['anomaly_percentage']:.2f}%")
    with col2:
        st.metric("Total Anomalies", f"{stats['anomaly_records']:,}")
    with col3:
        st.metric("Critical Anomalies", f"{stats['critical_anomalies']:,}")
    with col4:
        st.metric("High/Medium anomalies", f"{stats['high_anomalies'] + stats['medium_anomalies']:,}")

    st.write("")

    # 2. Hourly distribution of anomalies
    st.subheader("⏰ Anomalies Detected by Hour of Day")
    hourly = anomaly_data["hourly_analysis"]
    df_hourly = pd.DataFrame([
        {"Hour": int(k), "Count": v} for k, v in hourly.items()
    ])
    df_hourly = df_hourly.sort_values("Hour")
    
    fig_hourly = px.bar(
        df_hourly,
        x="Hour",
        y="Count",
        title="Hourly Distribution of Anomalies",
        color_discrete_sequence=["#DC2626"]
    )
    fig_hourly.update_layout(template="plotly_white", height=350)
    st.plotly_chart(fig_hourly, width="stretch")

    # 3. Scatter plot of anomaly events
    st.subheader("🔬 Anomaly Events Scatter Plot")
    high_risk_df = pd.DataFrame(anomaly_data["high_risk_records"])

    if not high_risk_df.empty:
        fig_scatter = px.scatter(
            high_risk_df,
            x="Global_active_power",
            y="Anomaly_Score",
            color="Severity",
            size="Global_intensity",
            hover_data=["Datetime", "Voltage"],
            title="Anomaly Events: Power vs. Anomaly Score",
            color_discrete_map={
                "Critical": "#DC2626",
                "High": "#F59E0B",
                "Medium": "#10B981",
            },
        )
        fig_scatter.update_layout(template="plotly_white", height=400)
        st.plotly_chart(fig_scatter, width="stretch")
    else:
        st.info("No anomaly events available to plot.")

    # 4. High Risk Records
    st.subheader("🚨 Top 10 Highest Risk Records")

    
    # Color coding helper
    def color_severity(val):
        color = 'white'
        if val == 'Critical':
            color = '#FEE2E2'
        elif val == 'High':
            color = '#FEF3C7'
        elif val == 'Medium':
            color = '#ECFDF5'
        return f'background-color: {color}'
        
    if hasattr(high_risk_df.style, 'map'):
        styled_df = high_risk_df.style.map(color_severity, subset=['Severity'])
    else:
        styled_df = high_risk_df.style.applymap(color_severity, subset=['Severity'])
    st.dataframe(styled_df, width="stretch", hide_index=True)

else:
    st.warning("Unable to load anomaly data.")

floating_ai()