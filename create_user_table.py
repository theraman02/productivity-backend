from database import Base, engine
from models import User

# Create users table
Base.metadata.create_all(bind=engine)
print("Users table created successfully!")
