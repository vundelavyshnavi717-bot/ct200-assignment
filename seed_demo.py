from app.db import init_db
from app.main import ingest
from app.db import SessionLocal
from pathlib import Path
init_db()
s=SessionLocal()
print('Use the API or scripts/demo.sh to ingest the supplied PDFs.')
