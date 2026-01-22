from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin")  # "admin" or "viewer"
    # Unique per user/company
    organization_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    role = Column(String, nullable=False)
    organization_id = Column(String, nullable=False,
                             index=True)  # Links to User's org


class WeeklyScore(Base):
    __tablename__ = "weekly_scores"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    week = Column(String, nullable=False)
    task_completion = Column(Float)
    speed = Column(Float)
    professionalism = Column(Float)
    activity = Column(Float)
    productivity_score = Column(Float)
    organization_id = Column(String, nullable=False,
                             index=True)  # Links to User's org
