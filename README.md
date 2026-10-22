# To-Do List Application — DevOps Mini-Project

## Problem statement

It is easy to lose track of small tasks when there is no simple place to record and review them. This project provides a small web-based to-do list and demonstrates how application source code moves through version control, automated tests, a Docker image, local deployment, and Prometheus monitoring.

## Objectives and features

- Build a clear, responsive to-do web app with Python and Flask.
- Add tasks, mark them complete, undo completion, and delete them.
- Store tasks in SQLite so they survive app/container restarts.
- Reject blank task names, limit names to 200 characters, and show a helpful not-found page for missing task IDs.
- Test the main behaviors and expose current task totals at `/metrics`.
- Run tests and build a Docker image automatically on GitHub pushes and pull requests.
- Run the app and Prometheus together locally with Docker Compose.

There are no accounts, cloud services, or Kubernetes. Grafana is not included in this small implementation.

## Technology stack

| Area | Tool |
| --- | --- |
| Web application | Python 3.12+, Flask (CI and Docker use Python 3.12) |
| Persistent storage | SQLite |
| Application server in Docker | Gunicorn |
| Automated tests | pytest |
| Container image and local deployment | Docker, Docker Compose |
| Monitoring | Prometheus |
| Source control and CI | Git, GitHub, GitHub Actions |

## Architecture

```text
Browser
  |  http://localhost:5000 (tasks)      http://localhost:9090 (queries)
  v                                             ^
Flask + Gunicorn -- /metrics ------------------|
  |                                             |
  +-- SQLite file in named Docker volume       |
                                                |
                     Prometheus scrapes app:5000 every 15 seconds

GitHub push / pull request
  -> GitHub Actions: install -> pytest -> docker build (no image push)
```

## Run locally with Python

Open this folder in VS Code, then open **Terminal → New Terminal**. These commands assume Windows PowerShell.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

The first command creates a private Python environment in `.venv`; the next two install the app and test packages there. The test command runs the automated checks. The final command starts the development server; open <http://127.0.0.1:5000> in your browser and press **Ctrl+C** in the terminal to stop it. The local database is created at `instance/tasks.sqlite3`.

If `py -3` is not recognized, install Python 3.12 or newer and select **Add Python to PATH** during setup, then reopen the VS Code terminal.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pytest -v
python -m flask --app app run --debug
```

The local development server is for this project demo. Docker runs the app with Gunicorn.

The test suite uses a separate temporary SQLite file for each test. Test runs do not add, edit, or delete tasks in `instance/tasks.sqlite3`.

## Git and GitHub

This folder is not currently a Git repository and has no configured remote. Create an empty repository on GitHub first; do not add a README there if you already have one in this folder. In the VS Code PowerShell terminal, run these grouped commits to keep the app, tests, container setup, and CI/documentation history understandable:

```powershell
git init
git branch -M main
git add app.py templates static requirements.txt .gitignore
git commit -m "Implement Flask to-do application"
git add tests requirements-dev.txt
git commit -m "Add isolated application tests"
git add Dockerfile .dockerignore compose.yaml
git commit -m "Containerize app and add local deployment"
git add prometheus.yml .github/workflows/ci.yml README.md
git commit -m "Add metrics CI workflow and project guide"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the example remote with **your own repository URL** copied from GitHub. These commands initialize version control, create commits grouped by project feature, connect the folder to your GitHub repository, and push the `main` branch. GitHub may ask you to authenticate. Do not put passwords, tokens, private keys, or other credentials in the repository. Commits are not a substitute for genuine participation: group members should contribute and explain their own work.

After the initial push, make small commits as you work on real changes. For each update, run `git status`, add the relevant files, commit with a short description of the change, and run `git push`.

## Docker deployment

Install and start Docker Desktop, wait until it reports that the Docker engine is running, and then use the VS Code PowerShell terminal in this folder.

```powershell
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f
```

`build` creates the app image. `up -d` starts the app and Prometheus in the background. `ps` shows whether the containers are running and whether the app passed its health check. `logs -f` follows their output; press **Ctrl+C** to stop following logs without stopping the containers.

Open <http://localhost:5000> for the to-do app. The `todo_data` named volume stores `tasks.sqlite3` outside the app container, so task data remains if you stop and recreate the containers. If the app is already running directly on port 5000, stop it with **Ctrl+C** before starting Compose, or Docker may not be able to bind that port.

To stop the containers but keep the saved tasks:

```powershell
docker compose down
```

To also permanently remove the named database volume and its tasks (optional, destructive):

```powershell
docker compose down --volumes
```

## Prometheus monitoring

Compose starts Prometheus at <http://localhost:9090>. Open <http://localhost:9090/targets> to check that the `todo-app` target is **UP**. The app's metrics endpoint is also available directly at <http://localhost:5000/metrics>.

| Prometheus query | Meaning |
| --- | --- |
| `todo_tasks_total` | Current total number of tasks |
| `todo_tasks_completed` | Current number of completed tasks |
| `todo_tasks_pending` | Current number of pending tasks |

To run a query, open <http://localhost:9090/>, enter `todo_tasks_total` or `todo_tasks_completed`, and click **Execute**. Metrics are collected every 15 seconds by default, so a task change can take up to one scrape interval to appear.

If a page does not load, first check `docker compose ps` and `docker compose logs app prometheus`. Confirm `/metrics` returns metric text at <http://localhost:5000/metrics>, then check <http://localhost:9090/targets> for the target health and any scrape error. Port 9090 is available only while Prometheus is running.

Grafana is not installed, configured, or verified here. This project demonstrates Prometheus metrics and its built-in query/graph view. The student brief also mentions Grafana and a dashboard/metric view, so check your instructor's rubric: if a Grafana dashboard is mandatory, that assignment item remains open and Grafana must be added and verified separately.

## What CI does

`.github/workflows/ci.yml` runs on every push and pull request. GitHub Actions checks out the code, sets up Python 3.12, installs the pinned dependencies, runs pytest, and builds the Docker image. It does **not** publish an image or require repository secrets.

This is **continuous integration (CI)**: checks and builds run automatically on GitHub after a push or pull request. It does not deploy the app. Starting `docker compose up -d` yourself is **local deployment**, not automatic continuous deployment (CD).

GitHub Actions runs only after the workflow and project are committed and pushed to GitHub. Open your repository's **Actions** tab, select **To-Do App CI**, and open a workflow run to see each step and its result. A green run is evidence that the tests and image build passed for that commit.

## Report and live-demo checklist

Use genuine results from your own run; this README is not evidence that commands or CI have already succeeded.

- [ ] Add the project title and your own group member names, IDs, and batch. The student brief expects a group of 2–3 from the same batch; coordinate the required contributions with your group.
- [ ] Explain the problem statement, objectives, requirements, app behavior, technology stack, and architecture.
- [ ] Show your GitHub repository and a meaningful commit history, with contributions from group members as required by your course.
- [ ] Show the GitHub Actions workflow and genuine passing test/build results from your repository.
- [ ] Run and show the Docker image and running containers; demonstrate that the app is accessible at `http://localhost:5000`; include deployment commands/details.
- [ ] Add a task, complete it, restart the app/container, and confirm the task is still saved.
- [ ] Show the Prometheus target as **UP** and query `todo_tasks_total` or `todo_tasks_completed`. The brief mentions Prometheus/Grafana; Grafana is not included in this project, so add and verify a Grafana dashboard if your instructor requires it.
- [ ] Capture genuine screenshots of the repository/commit history, Actions test/build results, Docker image and running containers, accessible app, and Prometheus target/query; include them with your report.
- [ ] Summarize implementation steps, configuration, test/deployment results, and conclusions in the report.
- [ ] Prepare and deliver the final presentation and a live end-to-end demo.

**Before submission:** fill in your own group details and capture genuine screenshots and results from your own GitHub and Docker runs. Do not present example instructions as proof of a successful run.
