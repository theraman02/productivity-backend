from database import SessionLocal
from models import Employee

db = SessionLocal()

employees = [
    Employee(name="Aarav Sharma", department="Engineering",
             role="Backend Developer"),
    Employee(name="Riya Patel", department="Engineering",
             role="Frontend Developer"),
    Employee(name="Kabir Singh", department="Product", role="Product Manager"),
    Employee(name="Ananya Gupta", department="Design", role="UI/UX Designer"),
    Employee(name="Rahul Verma", department="Marketing", role="Growth Analyst"),
]

db.add_all(employees)
db.commit()
db.close()

print("Sample employees inserted successfully.")
