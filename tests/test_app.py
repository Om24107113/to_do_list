import sqlite3

import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(tmp_path / "test-tasks.sqlite3"),
        }
    )
    return app.test_client()


def test_add_task(client):
    response = client.post("/tasks", data={"title": "Write project report"})

    assert response.status_code == 302
    page = client.get("/")
    assert b"Write project report" in page.data


def test_blank_task_is_ignored(client):
    client.post("/tasks", data={"title": "   "})

    page = client.get("/")
    assert b"Enter a task before adding it." in page.data
    assert b'class="task-title"' not in page.data


def test_complete_and_undo_task(client):
    client.post("/tasks", data={"title": "Review tests"})
    task_id = _task_id(client)

    client.post(f"/tasks/{task_id}/toggle")
    page = client.get("/")
    assert b'class="task-row is-complete"' in page.data

    client.post(f"/tasks/{task_id}/toggle")
    page = client.get("/")
    assert b"Review tests" in page.data
    assert b"completed" not in page.data


def test_delete_task(client):
    client.post("/tasks", data={"title": "Temporary task"})
    task_id = _task_id(client)

    response = client.post(f"/tasks/{task_id}/delete")

    assert response.status_code == 302
    assert b"Temporary task" not in client.get("/").data


def test_metrics_report_task_counts(client):
    client.post("/tasks", data={"title": "Pending task"})
    client.post("/tasks", data={"title": "Completed task"})
    task_ids = _task_ids(client)
    client.post(f"/tasks/{task_ids[1]}/toggle")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    assert b"todo_tasks_total 2.0" in response.data
    assert b"todo_tasks_completed 1.0" in response.data
    assert b"todo_tasks_pending 1.0" in response.data


def test_missing_task_id_returns_not_found(client):
    assert client.post("/tasks/999/toggle").status_code == 404
    assert client.post("/tasks/999/delete").status_code == 404


def _task_id(client):
    return _task_ids(client)[0]


def _task_ids(client):
    with sqlite3.connect(client.application.config["DATABASE"]) as database:
        return [
            row[0]
            for row in database.execute("SELECT id FROM tasks ORDER BY id").fetchall()
        ]
