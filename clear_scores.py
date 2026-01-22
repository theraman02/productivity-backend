from database import SessionLocal
from models import WeeklyScore

db = SessionLocal()

# Delete all scores
deleted = db.query(WeeklyScore).delete()
db.commit()

print(f"✅ Deleted {deleted} scores successfully!")
print("📋 Employees are still intact.")

db.close()
