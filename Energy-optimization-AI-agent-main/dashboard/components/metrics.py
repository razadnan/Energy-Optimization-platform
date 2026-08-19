import streamlit as st
from dashboard.utils.data_loader import load_usage_data


def current_usage():
    st.subheader("⚡ Peak Hour Analysis")

    active_id = st.session_state.get("active_dataset_id")
    usage_data = load_usage_data(active_id) if active_id else None

    if usage_data:
        peak_hour = usage_data["peak_usage"]["peak_hour"]
        peak_kw = usage_data["peak_usage"]["peak_hour_average_kw"]
        avg_kw = usage_data["consumption"]["average_daily_energy_kwh"] / 24.0
        
        pct_peak = int((avg_kw / peak_kw) * 100) if peak_kw > 0 else 0
        pct_peak = min(max(pct_peak, 0), 100)

        st.metric(
            "Peak load",
            f"{peak_kw:.2f} kW",
            help=f"Peak hour identified at {peak_hour}:00"
        )
        st.progress(pct_peak)
        st.caption(f"Average load is {pct_peak}% of peak load.")
    else:
        st.metric("Peak load", "--")
        st.progress(0)
        st.caption("No active dataset")