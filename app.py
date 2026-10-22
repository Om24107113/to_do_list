import os
import sqlite3
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest
from werkzeug.wrappers import Response


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-key"),
        DATABASE=os.environ.get(
            "SQLITE_DB_PATH", str(Path(app.instance_path) / "tasks.sqlite3")
        ),
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    database_path = Path(app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 200),
                completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0, 1))
            )
            """
        )

    registry = CollectorRegistry()
    total_tasks = Gauge(
        "todo_tasks_total",
        "Current number of tasks in the to-do list.",
        registry=registry,
    )
    completed_tasks = Gauge(
        "todo_tasks_completed",
        "Current number of completed tasks in the to-do list.",
        registry=registry,
    )
    pending_tasks = Gauge(
        "todo_tasks_pending",
        "Current number of pending tasks in the to-do list.",
        registry=registry,
    )
    app.config["METRICS_REGISTRY"] = registry

    @app.teardown_appcontext
    def close_db(_exception=None):
        database = g.pop("database", None)
        if database is not None:
            database.close()

    def get_db():
        if "database" not in g:
            g.database = sqlite3.connect(app.config["DATABASE"])
            g.database.row_factory = sqlite3.Row
        return g.database

    @app.get("/")
    def index():
        tasks = get_db().execute(
            "SELECT id, title, completed FROM tasks ORDER BY completed, id DESC"
        ).fetchall()
        return render_template("index.html", tasks=tasks)

    @app.post("/tasks")
    def add_task():
        title = request.form.get("title", "").strip()
        if not title:
            flash("Enter a task before adding it.", "error")
        elif len(title) > 200:
            flash("Tasks must be 200 characters or fewer.", "error")
        else:
            database = get_db()
            database.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
            database.commit()
            flash("Task added.", "success")
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/toggle")
    def toggle_task(task_id):
        database = get_db()
        cursor = database.execute(
            """
            UPDATE tasks
            SET completed = CASE completed WHEN 0 THEN 1 ELSE 0 END
            WHERE id = ?
            """,
            (task_id,),
        )
        if cursor.rowcount == 0:
            abort(404)
        database.commit()
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/delete")
    def delete_task(task_id):
        database = get_db()
        cursor = database.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            abort(404)
        database.commit()
        flash("Task deleted.", "success")
        return redirect(url_for("index"))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics():
        counts = get_db().execute(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(completed), 0) AS completed
            FROM tasks
            """
        ).fetchone()
        total = counts["total"]
        completed = counts["completed"]
        total_tasks.set(total)
        completed_tasks.set(completed)
        pending_tasks.set(total - completed)
        return Response(generate_latest(registry), content_type=CONTENT_TYPE_LATEST)

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
