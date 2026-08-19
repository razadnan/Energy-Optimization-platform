import pandas as pd

class FeatureEngineer:
    """
    Class to engineer time-based features from datetime column.
    """

    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Creates time-based features on the passed dataframe.
        Expects a 'Datetime' column to exist.
        """
        df = df.copy()
        df["Hour"] = df["Datetime"].dt.hour
        df["Day"] = df["Datetime"].dt.day
        df["Month"] = df["Datetime"].dt.month
        df["Weekday"] = df["Datetime"].dt.day_name()
        df["Is_Weekend"] = (
            df["Datetime"].dt.weekday >= 5
        ).astype(int)
        return df
