from database import Base, engine
from models import Employee, WeeklyScore

# Drop all tables
Base.metadata.drop_all(bind=engine)
print("Tables dropped successfully")

# Create all tables
Base.metadata.create_all(bind=engine)
print("Tables created successfully")
