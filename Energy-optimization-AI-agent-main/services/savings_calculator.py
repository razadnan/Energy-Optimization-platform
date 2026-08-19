from backend.config import config

class SavingsCalculator:
    """
    Performs energy savings and CO2 reduction calculations.
    """

    @staticmethod
    def calculate_savings(saving_percent: float, average_daily_kwh: float) -> dict:
        """
        Calculate daily, monthly, and yearly kWh savings and cost savings.
        """
        saving_percent = min(saving_percent, 30.0) # Cap at 30%

        daily_kwh = round(average_daily_kwh * saving_percent / 100.0, 2)
        monthly_kwh = round(daily_kwh * 30.0, 2)
        yearly_kwh = round(daily_kwh * 365.0, 2)

        rate = config.ELECTRICITY_RATE  # e.g., ₹8.0 per kWh

        daily_rupees = round(daily_kwh * rate, 2)
        monthly_rupees = round(monthly_kwh * rate, 2)
        yearly_rupees = round(yearly_kwh * rate, 2)

        return {
            "estimated_saving_percent": saving_percent,
            "daily_saving_kwh": daily_kwh,
            "monthly_saving_kwh": monthly_kwh,
            "yearly_saving_kwh": yearly_kwh,
            "estimated_daily_savings_rupees": daily_rupees,
            "estimated_monthly_savings_rupees": monthly_rupees,
            "estimated_yearly_savings_rupees": yearly_rupees
        }

    @staticmethod
    def calculate_co2_reduction(yearly_saving_kwh: float) -> dict:
        """
        Calculate yearly and monthly CO2 emission reductions.
        """
        co2_factor = config.CO2_PER_KWH # e.g., 0.82 kg CO2/kWh
        yearly_co2 = round(yearly_saving_kwh * co2_factor, 2)
        monthly_co2 = round((yearly_saving_kwh / 12.0) * co2_factor, 2)

        return {
            "estimated_yearly_co2_reduction_kg": yearly_co2,
            "estimated_monthly_co2_reduction_kg": monthly_co2
        }
