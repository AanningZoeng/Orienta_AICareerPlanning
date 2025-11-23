r"""Test Flask server configuration and frontend integration.

Run with: python tests\flask_integration_test.py

Tests:
- Flask app initializes correctly
- Static files are accessible (frontend)
- API endpoints return expected structure
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.api.server import app


def test_static_route():
    """Test that the root route serves index.html"""
    with app.test_client() as client:
        resp = client.get('/')
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        html = resp.get_data(as_text=True)
        assert 'AI Career Path Planner' in html, "index.html not served correctly"
        print("✅ Root route serves index.html")


def test_health_endpoint():
    """Test health check endpoint"""
    with app.test_client() as client:
        resp = client.get('/api/health')
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.get_json()
        assert 'status' in data, "Missing 'status' in health response"
        print(f"✅ Health endpoint OK: {data}")


def test_analyze_endpoint_structure():
    """Test analyze endpoint returns correct structure"""
    with app.test_client() as client:
        resp = client.post('/api/analyze', json={"query": "test query"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.get_json()
        assert 'majors' in data, "Missing 'majors' in response"
        assert isinstance(data['majors'], list), "'majors' must be a list"
        if data['majors']:
            major = data['majors'][0]
            assert 'name' in major, "Major missing 'name'"
            assert 'description' in major, "Major missing 'description'"
            assert 'resources' in major, "Major missing 'resources'"
        print(f"✅ Analyze endpoint returns correct structure ({len(data['majors'])} majors)")


def main():
    print("Testing Flask integration...\n")
    try:
        test_static_route()
        test_health_endpoint()
        test_analyze_endpoint_structure()
        print("\n✅ All Flask integration tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
