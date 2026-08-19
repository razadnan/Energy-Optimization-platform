import streamlit as st
from components.header import render_header
from components.sidebar import render_sidebar
from components.theme import configure_page
from dashboard.utils.data_loader import load_reports_data, load_insight_data
from components.floating_ai import floating_ai
configure_page()
render_sidebar()
render_header()

from dashboard.utils.data_loader import check_active_dataset_status
check_active_dataset_status()

st.title("📄 Audit Reports")

active_dataset_id = st.session_state.get("active_dataset_id")
if not active_dataset_id:
    st.warning("⚠️ No active dataset found. Please upload a dataset on the Overview page to unlock audit reports!")
    st.stop()

with st.spinner("Compiling Energy Intelligence Audit Report..."):
    report_data = load_reports_data(active_dataset_id)
    insight_data = load_insight_data(active_dataset_id)

if report_data:
    st.success("✅ Audit report generated successfully.")

    # PDF Download Button
    import requests
    from dashboard.utils.data_loader import get_auth_headers, API_BASE_URL
    pdf_bytes = None
    try:
        res = requests.get(f"{API_BASE_URL}/reports/download", headers=get_auth_headers(), timeout=10)
        if res.status_code == 200:
            pdf_bytes = res.content
    except Exception:
        pass
        
    if not pdf_bytes and active_dataset_id:
        try:
            from services.pdf_generator import PDFGenerator
            from backend.config import config
            pdf_dir = config.OUTPUT_DIR
            pdf_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = pdf_dir / f"report_{active_dataset_id}.pdf"
            PDFGenerator.generate_pdf(report_data["summary_markdown"], str(pdf_path))
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
        except Exception as e:
            st.error(f"Error generating fallback PDF: {e}")
            
    if pdf_bytes:
        st.download_button(
            label="📥 Download PDF Audit Report",
            data=pdf_bytes,
            file_name=f"energy_audit_report_{active_dataset_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # AI reasoning-layer banner — this is the InsightAgent's judgment,
    # not a fixed rule, surfaced directly (perceive -> reason -> act).
    if insight_data:
        alert_level = insight_data.get("alert_level", "Normal")
        source = insight_data.get("source", "llm")

        banner_style = {
            "Urgent": ("🔴", "#FEE2E2", "#991B1B", "#DC2626"),
            "Watch": ("🟠", "#FFFBEB", "#78350F", "#F59E0B"),
            "Normal": ("🟢", "#ECFDF5", "#065F46", "#10B981"),
        }.get(alert_level, ("🟢", "#ECFDF5", "#065F46", "#10B981"))

        icon, bg, text_color, border = banner_style
        source_note = (
            "AI-generated judgment" if source == "llm"
            else "deterministic fallback — no LLM key configured"
        )

        st.markdown(
            f"""
            <div style="padding:16px 20px; border-radius:8px; background-color:{bg};
                        border:1px solid {border}; margin-bottom:16px;">
                <h3 style="margin:0; color:{text_color};">{icon} Alert Level: {alert_level}</h3>
                <p style="margin:6px 0 0; color:{text_color};">
                    <b>Primary concern:</b> {insight_data.get("primary_concern", "")}
                </p>
                <p style="margin:4px 0 0; font-size:0.85em; color:{text_color}; opacity:0.8;">
                    {source_note}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("🧠 AI Insight Agent — Reasoning"):
            st.write(insight_data.get("reasoning", ""))
            st.write("**Executive Summary:**")
            st.write(insight_data.get("executive_summary", ""))

    st.write("")

    # Render the markdown report directly in Streamlit
    st.markdown(report_data["summary_markdown"])

else:
    st.warning("Unable to generate reports data.")
floating_ai()