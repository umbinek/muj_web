import pytest
from app import create_app
from models import Base

@pytest.fixture
def client():
    # Create aplication in test mode
    app = create_app()
    app.config['TESTING'] = True

    engine = app.SessionLocal.kw['bind']
    Base.metadata.create_all(bind=engine)
    # Run test client
    with app.test_client() as client:
        yield client

def test_api_status_success(client):
    """Tests whether the API returns the correct status during normal operation."""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'temperature' in data
    assert 'humidity' in data
    assert 'alarm' in data

def test_api_inject_data(client):
    """Tests the injection of test data."""
    test_payload = {"temp": 35.5, "hum": 60.0, "error": False}
    response = client.post('/api/test/inject_data', json=test_payload)
    
    if response.status_code != 404:
        assert response.status_code == 200
        status = client.get('/api/status').get_json()
        assert 'temperature' in status
        assert isinstance(status['temperature'], (int, float))

def test_api_air_quality_ingest(client):
    """Testing the endpoint for the new ESP32 with air quality monitoring."""
    payload = {"value": 850, "unit": "ppm", "sensor": "test-unit"}
    response = client.post('/api/air_quality', json=payload)
    
    if response.status_code != 404:
        assert response.status_code == 200
        assert response.get_json()['status'] == "OK"

def test_api_history_format(client):
    """Checks whether history returns a list."""
    response = client.get('/api/history')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_api_export_csv(client):
    """Tests whether the export returns a CSV file."""
    response = client.get('/api/export_csv')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    
    content = response.data.decode('utf-8')
    assert 'Teplota' in content
    assert 'Vlhkost' in content

def test_api_sensor_error_mode(client):
    """Tests the API's behavior during a simulated sensor error."""
    try:
        response = client.post('/api/test/inject_data', json={"error": True})
        if response.status_code != 404:
            status_response = client.get('/api/status')
            assert status_response.status_code == 500
            
            data = status_response.get_json()
            assert "Senzor nedostupný" in data.get("error", "")
    finally:
        client.post('/api/test/inject_data', json={"error": False})
