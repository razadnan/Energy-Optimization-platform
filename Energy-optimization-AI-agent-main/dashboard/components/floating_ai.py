import streamlit as st

def floating_ai():

    st.markdown("""
    <style>
    /* Specific class for the floating AI button */
    .floating-ai-btn {
        position: fixed !important;
        right: 28px;
        bottom: 28px;
        width: 148px !important;
        height: 148px !important;
        border-radius: 50% !important;
        border: 2px solid rgba(255,255,255,.08) !important;
        background: radial-gradient(circle at 30% 30%, #4F46E5, #2563EB, #111827) !important;
        color: white !important;
        font-size: 76px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        box-shadow: 0 12px 35px rgba(37,99,235,.35), 0 0 25px rgba(79,70,229,.30);
        transition: all .25s ease;
        z-index: 999999;
        cursor: pointer;
    }

    .floating-ai-btn:hover {
        transform: translateY(-4px) scale(1.08);
        box-shadow: 0 18px 45px rgba(37,99,235,.45), 0 0 35px rgba(79,70,229,.45);
        color: white !important;
        text-decoration: none !important;
    }

    .floating-ai-btn:active {
        transform: scale(.95);
    }
    </style>

    <a href="/AI_Assistant" target="_self" class="floating-ai-btn">🤖</a>
    """, unsafe_allow_html=True)