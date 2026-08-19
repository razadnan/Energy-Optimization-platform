import sys
from pathlib import Path

# Add project root and dashboard folder to python path to resolve all imports
root_path = str(Path(__file__).resolve().parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)
dashboard_path = str(Path(__file__).resolve().parent)
if dashboard_path not in sys.path:
    sys.path.insert(0, dashboard_path)

import streamlit as st
import requests
import time
import pandas as pd

from components.theme import configure_page
from components.sidebar import render_sidebar, upload_dataset_direct, API_BASE_URL
from backend.database import DatabaseManager

# Initialize the database schema (tables, indices) if they don't exist
try:
    DatabaseManager.initialize_db()
except Exception as e:
    st.error(f"Failed to initialize database schema: {e}")

# Page Config and Authentication Check
configure_page()

# Render Sidebar (which contains navigation links and active status)
render_sidebar()

# Main Page Layout
st.markdown(
    """
    <div style="padding-top: 10px; padding-bottom: 10px;">
        <h1 style="color:#22C55E; font-size:2.6rem; font-weight:700; margin-bottom:5px;">📥 Input Energy Data</h1>
        <p style="color:#9CA3AF; font-size:1.1rem;">Manage active telemetry datasets and trigger processing pipelines.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# Get active dataset details
active_id = st.session_state.get("active_dataset_id")
active_dataset_filename = None
active_dataset_status = None

if active_id:
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT filename, status FROM datasets WHERE id = ?", (active_id,))
        row = cursor.fetchone()
        if row:
            active_dataset_filename = row[0]
            active_dataset_status = row[1]
    except Exception as e:
        st.error(f"Error fetching dataset info: {e}")
    finally:
        conn.close()

# Shared file uploader function
def render_uploader_widget(widget_key):
    uploaded_file = st.file_uploader(
        "Choose an energy data file...",
        type=["csv", "xlsx", "xls"],
        key=widget_key,
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        file_key = f"uploaded_main_{uploaded_file.name}_{uploaded_file.size}"
        if not st.session_state.get(file_key):
            with st.status("🚀 Ingesting and processing dataset...", expanded=True) as status:
                status.write("Reading file bytes...")
                file_bytes = uploaded_file.read()
                
                user = st.session_state.get("user")
                user_id = user["id"] if user else 1
                
                status.write("Submitting to processing pipeline...")
                uploaded_id = None
                err = None
                
                # API Ingestion
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/datasets/upload",
                        headers={"X-User-ID": str(user_id)},
                        files={"file": (uploaded_file.name, file_bytes)},
                        timeout=15
                    )
                    if res.status_code == 200:
                        uploaded_id = res.json()["id"]
                    else:
                        err = res.json().get("detail", "Upload failed.")
                except Exception:
                    pass
                
                # Direct Ingestion Fallback
                if not uploaded_id and not err:
                    status.write("API offline; running direct background pipeline...")
                    uploaded_id, err = upload_dataset_direct(file_bytes, uploaded_file.name, user_id)
                
                if uploaded_id:
                    st.session_state[file_key] = True
                    st.session_state["active_dataset_id"] = uploaded_id
                    st.cache_data.clear()
                    status.update(label="🎉 Pipeline Ingestion Complete!", state="complete", expanded=False)
                    st.success("Redirecting to the Executive Overview dashboard...")
                    time.sleep(1.2)
                    st.switch_page("pages/01_Overview.py")
                else:
                    status.update(label="❌ Ingestion Failed", state="error")
                    st.error(err or "Failed to upload or parse the file. Check formatting.")

def render_format_specs_and_download():
    st.markdown("### 📋 Supported Format Specs")
    st.markdown(
        """
        Telemetry files must contain minute-level or hourly entries with:
        * **Datetime** (or separate `Date` and `Time` columns)
        * **Global_active_power** (active power in kW)
        * **Global_reactive_power** (reactive power in kW)
        * **Voltage** (voltage in Volts)
        * **Global_intensity** (current intensity in Amps)
        * **Sub_metering_1** (Kitchen consumption Wh)
        * **Sub_metering_2** (Laundry/Utility Wh)
        * **Sub_metering_3** (HVAC/Water heater Wh)
        """
    )
    
    # Render Download Sample Button
    sample_file_path = Path(__file__).resolve().parent.parent / "data" / "sample_data.csv"
    if sample_file_path.exists():
        try:
            with open(sample_file_path, "r", encoding="utf-8") as f:
                sample_csv = f.read()
            st.info("💡 **Quick Start**: Don't have a dataset? Download our pre-formatted 3-day sample telemetry data below to test the platform:")
            st.download_button(
                label="📥 Download 3-Day Sample CSV (Recommended)",
                data=sample_csv,
                file_name="energy_sample_3days.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        except Exception:
            pass

# Main Display Logic
if active_id and active_dataset_filename:
    left_col, right_col = st.columns([5, 3], gap="large")
    
    with left_col:
        st.markdown(f"### 📊 Ingested Energy Data: `{active_dataset_filename}`")
        
        status_color = "#22C55E" if active_dataset_status == "completed" else "#F59E0B"
        st.markdown(
            f"""
            <div style="background-color:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:15px; border-radius:10px; margin-bottom:20px;">
                <strong>Ingestion Status:</strong> 
                <span style="color:{status_color}; font-weight:600; text-transform:uppercase; padding:2px 8px; border-radius:4px; background:{status_color}20;">
                    {active_dataset_status}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Load active dataset preview
        with st.spinner("Loading telemetry rows..."):
            df = DatabaseManager.get_data(active_id)
            
        if not df.empty:
            st.caption(f"Showing preview of first 100 rows out of {len(df):,} total records.")
            
            # Select key columns for display to keep it neat
            display_cols = [
                "Datetime", "Global_active_power", "Global_reactive_power", 
                "Voltage", "Global_intensity", "Sub_metering_1", 
                "Sub_metering_2", "Sub_metering_3"
            ]
            st.dataframe(df[display_cols].head(100), use_container_width=True, height=350)
        else:
            st.warning("The dataset is currently processing or contains no telemetry rows.")
            
        st.write("")
        st.write("")
        
        # Option to upload data again
        with st.expander("🔄 Upload / Replace Telemetry Data", expanded=False):
            st.markdown("##### Upload a new dataset to replace the current active telemetry:")
            render_uploader_widget("uploader_replace")
            
    with right_col:
        render_format_specs_and_download()

else:
    left_col, right_col = st.columns([5, 3], gap="large")
    
    with left_col:
        st.markdown("### 📁 Upload Dataset")
        st.caption("Drag and drop your energy telemetry files below (CSV, XLS, or XLSX).")
        render_uploader_widget("uploader_initial")
        
    with right_col:
        render_format_specs_and_download()

st.divider()

# Educational Pipeline Column Blocks
st.markdown("### 🛠️ What happens to your data?")
col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown(
        """
        <div style="background-color:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:20px; border-radius:12px; height:100%;">
            <h4 style="color:#22C55E; margin-top:0;">🧹 1. Clean & Standardize</h4>
            <p style="font-size:0.9rem; color:#9CA3AF; margin-bottom:0;">
                The data preprocessor validates formatting, cleans negative outliers, standardizes column headings, and interpolates missing entries using median values.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div style="background-color:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:20px; border-radius:12px; height:100%;">
            <h4 style="color:#3B82F6; margin-top:0;">🤖 2. Forecasting & Isolation</h4>
            <p style="font-size:0.9rem; color:#9CA3AF; margin-bottom:0;">
                Facebook Prophet predicts daily loads for the next 30 days. Simultaneously, Isolation Forest maps anomalies and rates their urgency.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div style="background-color:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:20px; border-radius:12px; height:100%;">
            <h4 style="color:#F59E0B; margin-top:0;">💡 3. AI Recommendations</h4>
            <p style="font-size:0.9rem; color:#9CA3AF; margin-bottom:0;">
                Calculates direct savings potential in Rupees and matches it to CO₂ offsets. The Insight Agent summarizes findings to feed the AI chatbot.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )