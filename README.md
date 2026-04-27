# RunLogger

A Django web application for tracking running workouts with science-based training load analytics.

<img width="1724" height="934" alt="image" src="https://github.com/user-attachments/assets/919be843-4533-41a4-aaed-4b404dcbf736" />


## What it does

RunLogger helps runners monitor their training progress by combining a simple workout log with established athletic training principles. Each run you log is used to calculate your **Fitness (CTL)** and **Fatigue (ATL)** levels, giving you a data-driven view of whether your training is productive, building toward overreaching, or in recovery.

### Core Features

- **Workout Logging** — Record distance (km), duration, perceived effort (RPE 1-10), and optional notes for each run
- **Training Dashboard** — View your current fitness and fatigue levels at a glance, along with a 30-day interactive chart
- **Training Status** — Automatically determined based on your CTL/ATL ratio:
  - **Productive** (0.8–1.3) — optimal training zone
  - **Overreaching** (>1.5) — high injury risk, consider recovery
  - **Recovery** (<0.8) — deload phase
- **Pace & Load Metrics** — Per-run pace and session training load (duration × RPE)
- **CSV Import/Export** — Bulk import historical workouts or export your data for external analysis
- **Multi-user Support** — Each user's data is fully isolated with secure authentication

### Training Metrics Explained

| Metric | Description |
|--------|-------------|
| **Fitness (CTL)** | 6-week rolling average of training stress — your long-term aerobic base |
| **Fatigue (ATL)** | 7-day rolling average — your short-term accumulated fatigue |
| **Training Ratio** | CTL ÷ ATL — values between 0.8 and 1.3 indicate productive training |
| **Session Load** | Duration (minutes) × RPE — a proxy for training stress per workout |

## Tech Stack

- **Backend**: Django 6.0 (Python)
- **Database**: SQLite3
- **Frontend**: Tailwind CSS, Chart.js
- **Auth**: Django built-in authentication

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd RunLogger

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and set your Django secret key

# Run database migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

Open http://localhost:8000 and register an account to get started.

### Running Tests

```bash
python manage.py test
```

## CSV Import Format

When importing workouts via CSV, each row should follow this format:

```
date,distance_km,hours,minutes,seconds,rpe,notes
2024-01-15,10.5,1,2,30,7,Easy long run
```
