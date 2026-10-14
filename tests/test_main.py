from fastapi.testclient import TestClient

from main import app, tasks

client = TestClient(app)


def test_list_tasks_empty():
    tasks.clear()
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_create_task():
    tasks.clear()
    response = client.post("/tasks", json={"name": "Write tests"})
    assert response.status_code == 201
    assert response.json() == {"name": "Write tests", "done": False}