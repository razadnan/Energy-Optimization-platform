import streamlit as st

from components.header import render_header
from components.sidebar import render_sidebar
from components.theme import configure_page
from components.floating_ai import floating_ai

from backend.config import config


# -----------------------------------
# Page Configuration
# -----------------------------------

configure_page()

render_sidebar()

render_header()



# -----------------------------------
# Developer Mode
# -----------------------------------

developer_mode = getattr(
    config,
    "DEVELOPER_MODE",
    False
)



# -----------------------------------
# Page Title
# -----------------------------------

st.title("⚙️ System Settings")



# -----------------------------------
# Electricity Settings
# -----------------------------------

st.subheader("⚡ Electricity Tariff Rate")


rate_input = st.number_input(

    "Rate per kWh (₹)",

    min_value=1.0,

    max_value=50.0,

    value=float(config.ELECTRICITY_RATE),

    step=0.1
)



# -----------------------------------
# Sustainability Settings
# -----------------------------------

st.subheader("🌱 CO₂ Emissions Factor")


co2_input = st.number_input(

    "kg CO₂ emissions per kWh",

    min_value=0.01,

    max_value=5.0,

    value=float(config.CO2_PER_KWH),

    step=0.01
)



st.divider()



# -----------------------------------
# AI Configuration
# Developer Only
# -----------------------------------

# Keep existing values internally (hidden from UI)
api_key_input = config.ANTHROPIC_API_KEY
insight_model_input = config.INSIGHT_MODEL



# -----------------------------------
# Save .env Function
# -----------------------------------

def save_env_variables(variables: dict):

    env_path = config.BASE_DIR / ".env"


    lines = []


    if env_path.exists():

        try:

            with open(
                env_path,
                "r",
                encoding="utf-8"
            ) as file:

                lines = file.readlines()


        except Exception:

            pass



    updated_keys = set()

    new_lines = []



    for line in lines:


        stripped = line.strip()


        if (

            stripped

            and not stripped.startswith("#")

            and "=" in stripped

        ):


            key, value = stripped.split(
                "=",
                1
            )


            key = key.strip()



            if key in variables:


                new_lines.append(
                    f"{key}={variables[key]}\n"
                )


                updated_keys.add(key)

                continue



        new_lines.append(line)




    for key, value in variables.items():


        if key not in updated_keys:


            new_lines.append(
                f"{key}={value}\n"
            )



    try:


        with open(
            env_path,
            "w",
            encoding="utf-8"
        ) as file:


            file.writelines(new_lines)



    except Exception as e:


        st.error(
            f"❌ Failed saving configuration: {e}"
        )



# -----------------------------------
# Save Button
# -----------------------------------

if st.button(
    "💾 Save Configuration Settings",
    use_container_width=True
):


    config.ELECTRICITY_RATE = rate_input

    config.CO2_PER_KWH = co2_input


    save_env_variables({

        "ELECTRICITY_RATE":
        str(rate_input),


        "CO2_PER_KWH":
        str(co2_input)

    })

    # Trigger automatic data analysis and price recalculation for active dataset
    active_id = st.session_state.get("active_dataset_id")
    if active_id:
        with st.spinner("🔄 Recalculating price, data analysis, and savings..."):
            try:
                # 1. Fetch cached analysis, forecast, and anomaly results to avoid model re-fitting
                from dashboard.utils.data_loader import load_usage_data, load_forecast_data, load_anomaly_data
                usage_report = load_usage_data(active_id)
                forecast_report = load_forecast_data(active_id)
                anomaly_report = load_anomaly_data(active_id)
                
                # Fallback to direct calculation if not cached
                if not usage_report:
                    from analytics.usage_analysis import UsageAnalyzer
                    usage_report = UsageAnalyzer(dataset_id=active_id).generate_report()
                if not forecast_report:
                    from models.forecasting import ForecastingModel
                    forecast_report = ForecastingModel(dataset_id=active_id).run_pipeline()
                if not anomaly_report:
                    from models.anomaly_detection import AnomalyDetectionModel
                    anomaly_report = AnomalyDetectionModel(dataset_id=active_id).run_pipeline()
                
                # 2. Clear old recommendations, insight, and report caches
                from backend.cache import CacheManager
                import json
                
                cache_keys = [
                    f"dataset_{active_id}_recommendations",
                    f"dataset_{active_id}_insight",
                    f"dataset_{active_id}_report"
                ]
                for key in cache_keys:
                    cache_file = CacheManager.CACHE_DIR / f"{key}.json"
                    if cache_file.exists():
                        try:
                            cache_file.unlink()
                        except Exception:
                            pass
                            
                st.cache_data.clear()
                
                # 3. Recalculate Recommendation Engine
                from services.recommendation_engine import RecommendationEngine
                engine = RecommendationEngine(usage_report, forecast_report, anomaly_report, dataset_id=active_id)
                rec_report = engine.run_pipeline()
                
                # 4. Recalculate Insight Agent
                from agents.insight_agent import InsightAgent
                insight_report = InsightAgent().execute({
                    "usage": usage_report,
                    "forecast": forecast_report,
                    "anomaly": anomaly_report,
                    "recommendation": rec_report
                })
                
                # 5. Recalculate Markdown Audit Report
                from services.report_generator import ReportGenerator
                data = {
                    "usage": usage_report,
                    "forecast": forecast_report,
                    "anomaly": anomaly_report,
                    "recommendation": rec_report,
                    "insight": insight_report
                }
                generator = ReportGenerator(data)
                final_report = generator.generate_report()
                
                # 6. Recalculate PDF
                from services.pdf_generator import PDFGenerator
                from backend.config import config
                pdf_dir = config.OUTPUT_DIR
                pdf_dir.mkdir(parents=True, exist_ok=True)
                pdf_path = pdf_dir / f"report_{active_id}.pdf"
                PDFGenerator.generate_pdf(final_report.get("summary_markdown", ""), str(pdf_path))
                
                # 7. Update reports table in DB
                from backend.database import DatabaseManager
                conn = DatabaseManager.get_connection()
                cursor = conn.cursor()
                savings_json = json.dumps(rec_report.get("savings", {}))
                co2_json = json.dumps(rec_report.get("co2", {}))
                
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO reports (dataset_id, summary_markdown, alert_level, status, pdf_path, savings_json, co2_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        active_id,
                        final_report.get("summary_markdown", ""),
                        final_report.get("alert_level", "Normal"),
                        "completed",
                        str(pdf_path),
                        savings_json,
                        co2_json
                    )
                )
                conn.commit()
                conn.close()
                
                # 8. Store new results in CacheManager
                CacheManager.set(f"dataset_{active_id}_recommendations", rec_report)
                CacheManager.set(f"dataset_{active_id}_insight", insight_report)
                CacheManager.set(f"dataset_{active_id}_report", final_report)
                
                st.toast("⚡ Pricing and data analysis successfully recalculated!")
            except Exception as e:
                st.error(f"❌ Error during recalculation: {e}")


    st.success(
        "✅ Configuration saved successfully."
    )



# -----------------------------------
# Floating AI Button
# -----------------------------------

floating_ai()