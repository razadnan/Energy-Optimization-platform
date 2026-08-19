"""
Database Utility Layer (Multi-Tenant SaaS)
Energy Optimization Agent
"""

import sqlite3
import pandas as pd
from backend.config import config
from services.logger import setup_logger

logger = setup_logger("Database")


class DatabaseManager:
    """
    Manages SQLite database connections, schema initialization,
    and data storage/retrieval for multi-tenant energy consumption data.
    """

    @staticmethod
    def get_connection():
        """Get a connection to the SQLite database."""
        # Ensure parent directory exists
        config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(str(config.DATABASE_PATH))

    @staticmethod
    def initialize_db():
        """Create SaaS tables and indices if they do not exist."""
        logger.info("Initializing database schema for multi-tenancy...")
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        try:
            # Drop old single-tenant energy_data if it exists and doesn't support dataset_id
            cursor.execute("PRAGMA table_info(energy_data)")
            columns = [col[1] for col in cursor.fetchall()]
            if columns and "dataset_id" not in columns:
                logger.warning("Old single-tenant energy_data table found. Migrating table...")
                cursor.execute("DROP TABLE energy_data")

            # 1. Users Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 2. Datasets Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # 3. Energy Data Table (Multi-tenant)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS energy_data (
                    dataset_id INTEGER NOT NULL,
                    Datetime TEXT NOT NULL,
                    Global_active_power REAL,
                    Global_reactive_power REAL,
                    Voltage REAL,
                    Global_intensity REAL,
                    Sub_metering_1 REAL,
                    Sub_metering_2 REAL,
                    Sub_metering_3 REAL,
                    Hour INTEGER,
                    Day INTEGER,
                    Month INTEGER,
                    Weekday TEXT,
                    Is_Weekend INTEGER,
                    PRIMARY KEY (dataset_id, Datetime),
                    FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_energy_dataset_datetime ON energy_data(dataset_id, Datetime)")

            # 4. Predictions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    dataset_id INTEGER NOT NULL,
                    Date TEXT NOT NULL,
                    Predicted_Energy_kWh REAL NOT NULL,
                    Lower_Bound REAL NOT NULL,
                    Upper_Bound REAL NOT NULL,
                    PRIMARY KEY (dataset_id, Date),
                    FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
                )
            """)

            # 5. Recommendations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    estimated_saving_percent REAL NOT NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
                )
            """)

            # 6. Alerts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    value REAL,
                    description TEXT NOT NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
                )
            """)

            # 7. Reports Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    dataset_id INTEGER PRIMARY KEY,
                    summary_markdown TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pdf_path TEXT,
                    savings_json TEXT,
                    co2_json TEXT,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
                )
            """)

            conn.commit()
            logger.info("Database schema initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def save_data(df: pd.DataFrame, dataset_id: int):
        """
        Save the processed Pandas DataFrame to the SQLite database.
        """
        logger.info(f"Saving {len(df):,} records to database for dataset_id {dataset_id}...")
        conn = DatabaseManager.get_connection()
        try:
            df_to_save = df.copy()
            df_to_save["dataset_id"] = dataset_id
            
            if pd.api.types.is_datetime64_any_dtype(df_to_save["Datetime"]):
                df_to_save["Datetime"] = df_to_save["Datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

            cursor = conn.cursor()
            # Clear previous entries for this dataset_id to be idempotent
            cursor.execute("DELETE FROM energy_data WHERE dataset_id = ?", (dataset_id,))
            conn.commit()

            # Append the clean data
            df_to_save.to_sql("energy_data", conn, if_exists="append", index=False)
            logger.info("Data saved successfully.")
        except Exception as e:
            logger.error(f"Error saving data to database: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_data(dataset_id: int = None) -> pd.DataFrame:
        """
        Retrieve energy data from the SQLite database as a Pandas DataFrame.
        Falls back to loading the processed CSV file if no data is found in DB.
        """
        logger.info(f"Retrieving energy data from database for dataset_id {dataset_id}...")
        conn = DatabaseManager.get_connection()
        try:
            df = pd.DataFrame()
            if dataset_id is not None:
                df = pd.read_sql_query(
                    "SELECT * FROM energy_data WHERE dataset_id = ?", 
                    conn, 
                    params=[dataset_id],
                    parse_dates=["Datetime"]
                )
            
            # Fallback to CSV if DB query returned no rows or dataset_id is None
            if df.empty:
                csv_path = config.PROCESSED_DATA_DIR / "processed_energy_data.csv"
                if csv_path.exists():
                    logger.info(f"No records in DB for dataset_id {dataset_id}. Falling back to CSV: {csv_path}")
                    df = pd.read_csv(csv_path, parse_dates=["Datetime"])
                    if dataset_id is not None:
                        df["dataset_id"] = dataset_id
                else:
                    logger.warning(f"CSV fallback path {csv_path} does not exist.")
                    df = pd.read_sql_query("SELECT * FROM energy_data LIMIT 0", conn, parse_dates=["Datetime"])

            logger.info(f"Retrieved {len(df):,} records successfully.")
            return df
        except Exception as e:
            logger.error(f"Error retrieving data from database: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_active_dataset_id(user_id: int = None) -> int:
        """
        Get the ID of the latest successfully processed dataset for the user or system.
        """
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        try:
            if user_id is not None:
                cursor.execute(
                    "SELECT id FROM datasets WHERE user_id = ? AND status = 'completed' ORDER BY id DESC LIMIT 1",
                    (user_id,)
                )
            else:
                cursor.execute(
                    "SELECT id FROM datasets WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
                )
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error fetching active dataset: {e}")
            return None
        finally:
            conn.close()

