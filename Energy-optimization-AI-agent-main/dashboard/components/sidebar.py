"""
Premium Enterprise Sidebar (Multi-Tenant SaaS)
"""

import streamlit as st
import requests
import datetime
import threading
from backend.database import DatabaseManager
from services.preprocessing import DataPreprocessor

API_BASE_URL = "http://127.0.0.1:8000"


def get_user_datasets(user_id):
    """Retrieve user-specific datasets via API or direct database fallback."""
    try:
        res = requests.get(f"{API_BASE_URL}/datasets", headers={"X-User-ID": str(user_id)}, timeout=2)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    # Direct database fallback
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, user_id, filename, status, error_message, created_at FROM datasets WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        return [{
            "id": r[0],
            "user_id": r[1],
            "filename": r[2],
            "status": r[3],
            "error_message": r[4],
            "created_at": r[5]
        } for r in rows]
    except Exception:
        return []
    finally:
        conn.close()


def upload_dataset_direct(file_bytes, filename, user_id):
    """Saves and schedules dataset cleaning & AI pipeline run in a background thread."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        created_at = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO datasets (user_id, filename, status, created_at) VALUES (?, ?, ?, ?)",
            (user_id, filename, "uploading", created_at)
        )
        conn.commit()
        dataset_id = cursor.lastrowid
    except Exception as e:
        conn.close()
        return None, f"Database error: {str(e)}"

    raw_dir = DataPreprocessor().file_path.parent
    raw_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = raw_dir / f"dataset_{dataset_id}_{filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(file_bytes)
    except Exception as e:
        cursor.execute("UPDATE datasets SET status = 'failed', error_message = ? WHERE id = ?", (f"File save error: {str(e)}", dataset_id))
        conn.commit()
        conn.close()
        return None, f"Could not save file: {str(e)}"

    cursor.execute("UPDATE datasets SET status = 'cleaning' WHERE id = ?", (dataset_id,))
    conn.commit()
    conn.close()
    
    # Run the background pipeline
    from backend.routes.datasets import run_pipeline_async
    t = threading.Thread(target=run_pipeline_async, args=(dataset_id, str(temp_file_path)))
    t.start()
    
    return dataset_id, None


def render_sidebar():
    user = st.session_state.get("user")
    if not user:
        return

    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center;padding-top:10px;padding-bottom:15px;">
            <h2 style="margin-bottom:0px;color:#15803D;">⚡ Energy SaaS</h2>
            <p style="color:gray;margin-top:5px;">AI-Powered Optimization</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        # Sidebar navigation (moved to top of layout)
        pages = [
            ("📥", "Input Data", "app.py"),
            ("🏠", "Overview", "pages/01_Overview.py"),
            ("📈", "Usage Analytics", "pages/02_Usage_Analytics.py"),
            ("🔮", "Forecasting", "pages/03_Forecasting.py"),
            ("🚨", "Anomaly Detection", "pages/04_Anomaly_Detection.py"),
            ("💡", "Recommendations", "pages/05_Recommendations.py"),
            ("🌱", "Sustainability", "pages/06_Sustainability.py"),
            ("📄", "Reports", "pages/07_Reports.py"),
            ("⚙", "Settings", "pages/08_Settings.py"),
            ("💬", "AI Assistant", "pages/09_AI_Assistant.py")
        ]

        for icon, label, page in pages:
            st.page_link(
                page,
                label=f"{icon}  {label}"
            )

        st.divider()

        # User details (moved below navigation menu)
        st.markdown(f"👤 **{user['name']}**")
        st.caption(f"Organization: {user['organization']}")
        
        if st.button("Logout", key="logout_btn", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.divider()

        # Dataset Management (moved below user details)
        st.markdown("### 📂 Datasets")
        datasets = get_user_datasets(user["id"])
        
        if datasets:
            # Format list for selection
            options = []
            index_map = {}
            default_index = 0
            
            for idx, d in enumerate(datasets):
                status_emoji = "⏳" if d["status"] in ["uploading", "cleaning", "processing"] else "✅" if d["status"] == "completed" else "❌"
                label = f"{status_emoji} {d['filename']}"
                options.append(label)
                index_map[label] = d["id"]
                
                # Default selection to current active dataset if still in list
                if d["id"] == st.session_state.get("active_dataset_id"):
                    default_index = idx
                    
            selected_label = st.selectbox(
                "Active Dataset",
                options,
                index=default_index,
                key="sidebar_dataset_select"
            )
            
            new_dataset_id = index_map[selected_label]
            if st.session_state.get("active_dataset_id") != new_dataset_id:
                st.session_state["active_dataset_id"] = new_dataset_id
                st.cache_data.clear()
                st.rerun()
                
            # If the active dataset has failed, show error message
            active_ds = next((d for d in datasets if d["id"] == new_dataset_id), None)
            if active_ds and active_ds["status"] == "failed":
                st.error(f"Processing Failed:\n{active_ds['error_message']}")
            elif active_ds and active_ds["status"] in ["uploading", "cleaning", "processing"]:
                st.warning(f"Processing status: {active_ds['status']}")
                if st.button("Refresh Status", use_container_width=True):
                    st.rerun()
        else:
            st.info("No datasets uploaded yet. Click 'Input Data' to upload.")
            st.session_state["active_dataset_id"] = None

        st.divider()

        st.markdown("### 🤖 AI Status")
        # Custom premium status pill
        st.markdown(
            """
            <div style="background-color:rgba(34, 197, 94, 0.1); border:1px solid #22C55E; color:#22C55E; padding:8px 12px; border-radius:8px; font-weight:600; text-align:center; font-size:0.9em;">
                🟢 System Online
            </div>
            """,
            unsafe_allow_html=True
        )
        st.caption("v1.0.0 | © 2026 Energy SaaS")
