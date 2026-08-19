import streamlit as st
from components.header import render_header
from components.sidebar import render_sidebar
from components.theme import configure_page
from dashboard.utils.data_loader import send_chat_message, load_insight_data

configure_page()
render_sidebar()
render_header()

from dashboard.utils.data_loader import check_active_dataset_status
check_active_dataset_status()

st.title("💬 AI Energy Assistant")
st.caption(
    "Ask about what the pipeline found - usage patterns, forecasts, "
    "anomalies, risks, or how to act on the recommendations. Answers are "
    "grounded in your actual dashboard data, not invented."
)

# Show current alert level so the chat opens with context, same source of
# truth as the Reports page banner.
active_dataset_id = st.session_state.get("active_dataset_id")
if not active_dataset_id:
    st.warning("⚠️ No active dataset found. Please upload a dataset on the Overview page to unlock the AI Assistant!")
    st.stop()

if st.session_state.get("last_active_dataset_id") != active_dataset_id:
    st.session_state.chat_history = []
    st.session_state.last_active_dataset_id = active_dataset_id

insight_data = load_insight_data(active_dataset_id)
if insight_data:
    alert_level = insight_data.get("alert_level", "Normal")
    icon = {"Urgent": "🔴", "Watch": "🟠", "Normal": "🟢"}.get(alert_level, "🟢")
    st.info(f"{icon} Current alert level: **{alert_level}** — {insight_data.get('primary_concern', '')}")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Render prior turns
for turn in st.session_state.chat_history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])

# Suggested starter questions on first load
if not st.session_state.chat_history:
    st.markdown("**Try asking:**")
    cols = st.columns(3)
    starters = [
        "What's the biggest risk right now?",
        "Why were anomalies flagged this month?",
        "How do I reduce my energy costs?",
    ]
    for col, starter in zip(cols, starters):
        if col.button(starter, width="stretch"):
            st.session_state.pending_message = starter

user_message = st.chat_input("Ask about your energy data...")

# A starter button click behaves the same as typing the message
if "pending_message" in st.session_state:
    user_message = st.session_state.pop("pending_message")

if user_message:
    st.session_state.chat_history.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = send_chat_message(user_message, st.session_state.chat_history[:-1], dataset_id=active_dataset_id)
            reply = result.get("reply", "Sorry, I couldn't generate a response.")
            source = result.get("source", "fallback")
        st.markdown(reply)
        if source == "fallback":
            st.caption("⚠️ Running in fallback mode - set GEMINI_API_KEY for full reasoning.")

    st.session_state.chat_history.append({"role": "assistant", "content": reply})

if st.session_state.chat_history:
    if st.button("🗑️ Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()
