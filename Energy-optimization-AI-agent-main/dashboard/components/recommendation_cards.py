import streamlit as st
from dashboard.utils.data_loader import load_recommendation_data


def recommendations():
    st.subheader("💡 Today's Top Recommendations")

    active_id = st.session_state.get("active_dataset_id")
    recs_data = load_recommendation_data(active_id) if active_id else None
    
    if recs_data and recs_data.get("recommendations"):
        recs_list = recs_data["recommendations"]
        # Take the top 2 recommendations
        for rec in recs_list[:2]:
            st.info(
                f"**[{rec['category']}]**  \n"
                f"{rec['recommendation']}  \n"
                f"Est. Savings: **{rec['estimated_saving_percent']}%** | Priority: **{rec['priority']}**"
            )
    else:
        st.info("No recommendations available. Please select or upload a dataset.")