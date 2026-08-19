import streamlit as st
import requests
from components.sidebar import upload_dataset_direct
from pathlib import Path

API_BASE_URL = "http://127.0.0.1:8000"


def render_onboarding_wizard():
    user = st.session_state.get("user")
    if not user:
        return

    # Read sample data CSV file
    sample_file_path = Path(__file__).parents[2] / "data" / "sample_data.csv"
    sample_csv_content = ""
    if sample_file_path.exists():
        try:
            with open(sample_file_path, "r") as f:
                sample_csv_content = f.read()
        except Exception:
            pass

    st.markdown(
        f"""
        <div style="background-color:#1E293B; padding:30px; border-radius:15px; border:1px solid #334155; margin-bottom:25px; color:#F8FAFC;">
            <h2 style="margin-top:0px;color:#10B981;font-size:28px;">👋 Welcome to QuickCart Energy SaaS, {user['name']}!</h2>
            <p style="font-size:16px;color:#94A3B8;margin-bottom:20px;">
                Before our AI agents can generate optimization recommendations, build forecasting models, and flag anomalies, you need to upload your energy usage data. Follow the simple guide below to get started.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown(
            """
            <h3 style="color:#F1F5F9;font-size:20px;margin-bottom:15px;border-bottom:2px solid #10B981;padding-bottom:5px;">📋 Step-by-Step Instructions</h3>
            
            <ol style="color:#E2E8F0; line-height:1.6; font-size:15px; padding-left:20px;">
                <li style="margin-bottom:12px;">
                    <strong>Download Sample Dataset:</strong> Use the button below to retrieve a correctly formatted template CSV.
                </li>
                <li style="margin-bottom:12px;">
                    <strong>Prepare Your Energy Log:</strong> Format your daily or hourly consumption data with these exact column headers:
                    <ul style="padding-left:20px; margin-top:5px; color:#94A3B8;">
                        <li><code>Datetime</code> (format: YYYY-MM-DD HH:MM:SS)</li>
                        <li><code>Global_active_power</code> (Active power in kW)</li>
                        <li><code>Global_reactive_power</code> (Reactive power in kW)</li>
                        <li><code>Voltage</code> (V)</li>
                        <li><code>Global_intensity</code> (Amps)</li>
                        <li><code>Sub_metering_1, Sub_metering_2, Sub_metering_3</code> (Sub-meter loads)</li>
                    </ul>
                </li>
                <li style="margin-bottom:12px;">
                    <strong>Upload to the Dashboard:</strong> Drag and drop your file into the uploader on the right.
                </li>
            </ol>
            """,
            unsafe_allow_html=True
        )

        if sample_csv_content:
            st.download_button(
                label="📥 Download Sample CSV Template",
                data=sample_csv_content,
                file_name="sample_energy_data.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.error("Sample CSV file not found on server.")

    with col2:
        st.markdown(
            """
            <h3 style="color:#F1F5F9;font-size:20px;margin-bottom:15px;border-bottom:2px solid #10B981;padding-bottom:5px;">🚀 Upload Your Dataset</h3>
            """,
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "Upload your energy log (CSV/Excel)",
            type=["csv", "xlsx", "xls"],
            key="onboarding_file_uploader",
            help="Supported file types: CSV, XLS, XLSX"
        )

        if uploaded_file:
            # Check if this file has already been processed to prevent infinite loop on rerun
            file_key = f"uploaded_onboard_{uploaded_file.name}_{uploaded_file.size}"
            if not st.session_state.get(file_key):
                file_bytes = uploaded_file.read()

                uploaded_id = None
                err = None

                with st.spinner("Uploading and starting the multi-agent AI cleaning pipeline..."):
                    # API upload
                    try:
                        res = requests.post(
                            f"{API_BASE_URL}/datasets/upload",
                            headers={"X-User-ID": str(user["id"])},
                            files={"file": (uploaded_file.name, file_bytes)},
                            timeout=10
                        )
                        if res.status_code == 200:
                            uploaded_id = res.json()["id"]
                        else:
                            err = res.json().get("detail", "Upload failed.")
                    except Exception:
                        pass

                    # Fallback to direct upload
                    if not uploaded_id and not err:
                        uploaded_id, err = upload_dataset_direct(file_bytes, uploaded_file.name, user["id"])

                if uploaded_id:
                    st.session_state[file_key] = True
                    st.session_state["active_dataset_id"] = uploaded_id
                    st.cache_data.clear()
                    st.toast("File uploaded successfully! Redirecting...")
                    st.success("Dataset registered. Starting AI Analytics and Forecasting pipeline!")
                    st.rerun()
                else:
                    st.error(err or "Upload failed. Please ensure file structure matches instructions.")
