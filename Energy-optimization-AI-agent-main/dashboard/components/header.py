import streamlit as st


def render_header():

    left, right = st.columns([5,1])

    with left:

        st.title("⚡ Energy Intelligence Center")

        st.caption(
            "AI-Powered Energy Optimization Platform"
        )

    with right:

        st.metric(

            "System",

            "Online",

            "✓"

        )

    st.divider()