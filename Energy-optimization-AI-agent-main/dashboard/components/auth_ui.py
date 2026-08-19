import streamlit as st
import requests
import sqlite3
import datetime
from backend.routes.auth import hash_password, verify_password
from backend.database import DatabaseManager

API_BASE_URL = "http://127.0.0.1:8000"


def authenticate_direct(email, password):
    """Authenticate directly against SQLite as a robust fallback."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, email, password, organization, created_at FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            user_id, name, email_val, hashed_pw, org, created_at = row
            if verify_password(password, hashed_pw):
                return {
                    "id": user_id,
                    "name": name,
                    "email": email_val,
                    "organization": org,
                    "created_at": created_at
                }
    except Exception as e:
        st.error(f"Fallback DB error: {e}")
    finally:
        conn.close()
    return None


def register_direct(name, email, password, org):
    """Register directly against SQLite as a robust fallback."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return None, "Email is already registered."
            
        hashed = hash_password(password)
        created_at = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO users (name, email, password, organization, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email, hashed, org, created_at)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "name": name,
            "email": email,
            "organization": org,
            "created_at": created_at
        }, None
    except Exception as e:
        conn.rollback()
        return None, f"Fallback DB error: {str(e)}"
    finally:
        conn.close()


def show_login_interface():
    # Centered modern layout
    st.markdown(
        """
        <div style="text-align:center;padding:10px 0 30px 0;">
        <h1 style="color:#10B981;font-size:36px;margin-bottom:0px;">⚡ Energy SaaS Platform</h1>
        <p style="color:#6B7280;font-size:16px;">Enterprise AI Energy Analytics & Forecasting</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["🔒 Sign In", "📝 Sign Up"])

    with tab1:
        st.markdown("### Sign In to Your Account")
        login_email = st.text_input("Email Address", key="login_email_input")
        login_password = st.text_input("Password", type="password", key="login_password_input")
        
        if st.button("Sign In", type="primary", use_container_width=True):
            if not login_email or not login_password:
                st.error("Please fill in all fields.")
            else:
                user = None
                # Try API login
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/auth/login",
                        json={"email": login_email, "password": login_password},
                        timeout=3
                    )
                    if res.status_code == 200:
                        user = res.json()
                except Exception:
                    pass
                
                # Fallback to direct DB auth
                if not user:
                    user = authenticate_direct(login_email, login_password)

                if user:
                    st.session_state["user"] = user
                    # Resolve active dataset id for user
                    active_ds = DatabaseManager.get_active_dataset_id(user["id"])
                    st.session_state["active_dataset_id"] = active_ds
                    st.cache_data.clear()
                    st.success("Successfully logged in!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with tab2:
        st.markdown("### Create New SaaS Account")
        reg_name = st.text_input("Full Name")
        reg_email = st.text_input("Email Address")
        reg_password = st.text_input("Password", type="password")
        
        org_type = st.selectbox(
            "Organization Type",
            ["Home User", "Factory", "Hospital", "Office", "University"]
        )
        reg_org = st.text_input("Organization Name", placeholder="e.g., Green Energy Corp")

        if st.button("Create Account", use_container_width=True):
            if not reg_name or not reg_email or not reg_password or not reg_org:
                st.error("Please fill in all fields.")
            else:
                user = None
                err = None
                # Try API register
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/auth/register",
                        json={
                            "name": reg_name,
                            "email": reg_email,
                            "password": reg_password,
                            "organization": f"{org_type} - {reg_org}"
                        },
                        timeout=3
                    )
                    if res.status_code == 200:
                        user = res.json()
                    else:
                        err = res.json().get("detail", "Registration failed.")
                except Exception:
                    pass

                # Fallback to direct DB register
                if not user and not err:
                    user, err = register_direct(reg_name, reg_email, reg_password, f"{org_type} - {reg_org}")

                if user:
                    st.session_state["user"] = user
                    st.session_state["active_dataset_id"] = None
                    st.success("Account created successfully!")
                    st.rerun()
                else:
                    st.error(err or "Registration failed.")
