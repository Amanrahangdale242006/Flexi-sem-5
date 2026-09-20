import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database configuration
DATABASE_PATH = os.path.join(BASE_DIR, "interview_scheduler.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Application configurations
APP_NAME = "AutoSchedule AI - Interview Scheduler"
APP_DESCRIPTION = "Automated Intelligent Interview Scheduling & Evaluation System"
APP_VERSION = "1.0.0"

# Interview settings
DEFAULT_INTERVIEW_DURATION_MINUTES = 45
BUFFER_TIME_MINUTES = 15
DEFAULT_WORKING_HOURS_START = 9  # 9 AM
DEFAULT_WORKING_HOURS_END = 18    # 6 PM
