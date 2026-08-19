import streamlit as st

from components.sidebar import render_sidebar
from components.theme import configure_page
from components.header import render_header
from components.kpi_cards import render_kpi_cards
from components.charts import daily_usage_chart
from components.metrics import current_usage
from components.agent_pipeline import render_pipeline
from components.recommendation_cards import recommendations
from components.onboarding import render_onboarding_wizard
from components.floating_ai import floating_ai


configure_page()
render_sidebar()
render_header()

from dashboard.utils.data_loader import check_active_dataset_status
check_active_dataset_status()

active_dataset_id = st.session_state.get("active_dataset_id")

if active_dataset_id is None:
    render_onboarding_wizard()
else:
    render_kpi_cards()

    st.write("")

    left, right = st.columns([2,1])

    with left:

        daily_usage_chart()

    with right:

        current_usage()

    st.write("")

    render_pipeline()

    st.write("")

    recommendations()

    floating_ai()

