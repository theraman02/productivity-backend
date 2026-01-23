from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    primary_organization_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    organization_id = Column(String, ForeignKey(
        'organizations.id'), index=True)
    role = Column(String, default='viewer')
    joined_at = Column(DateTime, default=datetime.utcnow)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    role = Column(String, nullable=False)
    organization_id = Column(String, ForeignKey(
        'organizations.id'), nullable=False, index=True)


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
    organization_id = Column(String, ForeignKey(
        'organizations.id'), nullable=False, index=True)
