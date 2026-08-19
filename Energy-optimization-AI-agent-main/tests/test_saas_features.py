import io
import pytest
from fastapi.testclient import TestClient
from backend.api import app
from backend.database import DatabaseManager

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Clear database tables before each test run."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM datasets")
    cursor.execute("DELETE FROM energy_data")
    cursor.execute("DELETE FROM reports")
    conn.commit()
    conn.close()


def test_auth_registration_and_login():
    # 1. Register a new user
    reg_response = client.post(
        "/auth/register",
        json={
            "name": "Alice Smith",
            "email": "alice@example.com",
            "password": "securepassword123",
            "organization": "University - Tech Dept"
        }
    )
    assert reg_response.status_code == 200
    reg_data = reg_response.json()
    assert "id" in reg_data
    assert reg_data["email"] == "alice@example.com"
    assert reg_data["organization"] == "University - Tech Dept"

    # 2. Duplicate registration should fail
    dup_response = client.post(
        "/auth/register",
        json={
            "name": "Alice Smith",
            "email": "alice@example.com",
            "password": "differentpassword",
            "organization": "University - Tech Dept"
        }
    )
    assert dup_response.status_code == 400

    # 3. Login with correct credentials
    login_response = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": "securepassword123"
        }
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["id"] == reg_data["id"]

    # 4. Login with invalid password
    bad_login = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": "wrongpassword"
        }
    )
    assert bad_login.status_code == 401


def test_dataset_upload_and_pdf_download():
    # 1. Register and get user ID
    reg_res = client.post(
        "/auth/register",
        json={
            "name": "Bob Jones",
            "email": "bob@example.com",
            "password": "password123",
            "organization": "Factory - Production"
        }
    )
    user_id = reg_res.json()["id"]

    # Mock dataset file (CSV content)
    csv_content = (
        "Datetime,Global_active_power,Global_reactive_power,Voltage,Global_intensity,Sub_metering_1,Sub_metering_2,Sub_metering_3\n"
        "2006-12-16 17:00:00,4.216,0.418,234.84,18.4,0,1,17\n"
        "2006-12-17 17:00:00,5.360,0.436,233.63,23.0,0,1,16\n"
        "2006-12-18 17:00:00,3.120,0.200,235.00,14.0,0,0,15\n"
        "2006-12-19 17:00:00,4.500,0.300,234.50,19.0,0,1,16\n"
    )
    file_tuple = ("test_data.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")

    # 2. Upload dataset with X-User-ID header
    upload_res = client.post(
        "/datasets/upload",
        headers={"X-User-ID": str(user_id)},
        files={"file": file_tuple}
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert "id" in upload_data
    assert upload_data["status"] == "uploading"

    # 3. Retrieve datasets list for the user
    list_res = client.get("/datasets", headers={"X-User-ID": str(user_id)})
    assert list_res.status_code == 200
    datasets_list = list_res.json()
    assert len(datasets_list) == 1
    assert datasets_list[0]["id"] == upload_data["id"]

    # 4. Download PDF report for this dataset (falls back to generating default/seeding)
    pdf_res = client.get("/reports/download", headers={"X-User-ID": str(user_id), "X-Dataset-ID": str(upload_data["id"])})
    if pdf_res.status_code != 200:
        print("ERROR RESPONSE:", pdf_res.text)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 0
