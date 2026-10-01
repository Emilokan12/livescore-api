from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_unknown_team_returns_404():
    response = client.get("/games/basketball/team/xyznotateam")
    assert response.status_code == 404

def test_games_returns_list():
    response = client.get("/games/basketball")
    assert response.status_code == 200
    assert isinstance(response.json(), list)