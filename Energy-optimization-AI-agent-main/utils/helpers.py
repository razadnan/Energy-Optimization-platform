import numpy as np
import pandas as pd

def convert_numpy_types(obj):
    """
    Recursively converts numpy types (float64, int64, etc.) to native Python types.
    Also formats floats to round to 4 decimal places where applicable.
    Converts dictionary keys to string if they are date/timestamp/numpy types.
    """
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if isinstance(k, pd.Timestamp):
                k_str = k.isoformat()
            elif hasattr(k, "isoformat"):
                k_str = k.isoformat()
            elif isinstance(k, (np.integer, np.floating)):
                k_str = str(convert_numpy_types(k))
            else:
                k_str = str(k)
            new_dict[k_str] = convert_numpy_types(v)
        return new_dict
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(v) for v in list(obj))
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(round(obj, 4))
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, pd.Series):
        return convert_numpy_types(obj.to_dict())
    elif isinstance(obj, pd.DataFrame):
        return convert_numpy_types(obj.to_dict(orient="records"))
    return obj
