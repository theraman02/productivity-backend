from database import Base, engine
from models import Employee, WeeklyScore

Base.metadata.create_all(bind=engine)
print("Tables created successfully")
