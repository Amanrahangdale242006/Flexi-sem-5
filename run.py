import sys
import os
import uvicorn
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.database import engine, Base, SessionLocal
from backend.app.services.seed_data import seed_database

def print_banner():
    banner = """
=============================================================================
   _         _        ____       _              _       _        _    ___ 
  / \  _   _| |_ ___ / ___|  ___| |__   ___  __| |_   _| | ___  / \  |_ _|
 / _ \| | | | __/ _ \\___ \ / __| '_ \ / _ \/ _` | | | | |/ _ \/ _ \  | | 
/ ___ \ |_| | || (_) |___) | (__| | | |  __/ (_| | |_| | |  __/ ___ \ | | 
/_/   \_\__,_|\__\___/|____/ \___|_| |_|\___|\__,_|\__,_|_|\___/_/   \_\___|

             AUTOMATED INTERVIEW SCHEDULING SYSTEM
                   College Project Edition
=============================================================================
* Recruiter Dashboard : http://127.0.0.1:8000/
* Interactive API Docs : http://127.0.0.1:8000/docs
* Database Engine      : SQLite (Local)
* Press Ctrl + C to stop the server
=============================================================================
"""
    print(banner)

def main():
    print("[*] Initializing Database & Schema...")
    Base.metadata.create_all(bind=engine)

    print("[*] Checking / Seeding Demo Presentation Data...")
    db = SessionLocal()
    try:
        seed_database(db)
        print("[+] Demo data ready! (Interviewers, Jobs, Candidates & Slots configured)")
    finally:
        db.close()

    print_banner()

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=False if os.environ.get("PORT") else True
    )

if __name__ == "__main__":
    main()
