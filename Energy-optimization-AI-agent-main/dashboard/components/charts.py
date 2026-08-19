import streamlit as st
import plotly.express as px
import pandas as pd
from dashboard.utils.data_loader import load_usage_data


def daily_usage_chart():
    active_id = st.session_state.get("active_dataset_id")
    usage_data = load_usage_data(active_id) if active_id else None
    
    if usage_data:
        daily_trend = usage_data["trends"]["daily_trend"]
        df = pd.DataFrame([
            {"Date": k, "Energy (kWh)": v} for k, v in daily_trend.items()
        ])
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        
        # Display the last 14 days for dashboard overview readability
        df = df.tail(14)
        
        fig = px.line(
            df,
            x="Date",
            y="Energy (kWh)",
            markers=True,
            title="Recent Daily Energy Consumption (Last 14 Days)",
            color_discrete_sequence=["#10B981"]
        )
    else:
        df = pd.DataFrame({"Date": [], "Energy (kWh)": []})
        fig = px.line(df, x="Date", y="Energy (kWh)", title="No Active Dataset")
        
    fig.update_layout(
        height=400,
        template="plotly_white"
    )
    st.plotly_chart(
        fig,
        use_container_width=True
    )