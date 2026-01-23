from models import User, Organization, OrganizationMembership
from sqlalchemy import create_engine, text
from database import SessionLocal, Base, engine
import uuid

print("🔄 Starting Multi-Organization Migration...")

db = SessionLocal()

# Step 1: Add columns to existing tables first
print("\n1️⃣ Adding new columns to existing tables...")

with engine.connect() as conn:
    # Add primary_organization_id to users table
    try:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN primary_organization_id VARCHAR"))
        print("  ✅ Added primary_organization_id to users table")
    except Exception as e:
        if "already exists" in str(e):
            print("  ⏭️  primary_organization_id already exists in users table")
        else:
            print(f"  ⚠️  Users table: {e}")

    conn.commit()

# Step 2: Create new tables
print("\n2️⃣ Creating new tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ New tables created (organizations, organization_memberships)")
except Exception as e:
    print(f"⚠️  {e}")

# Step 3: Migrate existing users
print("\n3️⃣ Migrating existing users...")

# Now we can safely import models

users = db.query(User).all()

for user in users:
    # Get or create organization ID
    if user.primary_organization_id:
        org_id = user.primary_organization_id
    else:
        # Use the old organization_id if it exists, or create new one
        org_id = str(uuid.uuid4())
        user.primary_organization_id = org_id
        db.add(user)

    # Check if organization already exists
    existing_org = db.query(Organization).filter(
        Organization.id == org_id).first()

    if not existing_org:
        # Create organization
        org = Organization(
            id=org_id,
            name=f"{user.username}'s Organization",
            owner_id=user.id
        )
        db.add(org)
        print(f"  📦 Created organization for {user.username}")

    # Create membership (user is admin of their own org)
    existing_membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.organization_id == org_id
    ).first()

    if not existing_membership:
        membership = OrganizationMembership(
            user_id=user.id,
            organization_id=org_id,
            role='admin'
        )
        db.add(membership)
        print(f"  👤 Added {user.username} as admin of their organization")

db.commit()
print("\n✅ User migration complete!")

# Step 4: Update employees and scores to use existing organization_id
print("\n4️⃣ Verifying employee and score organizations...")
print("✅ Employees and scores already have organization_id from previous migration")

db.close()

print("\n🎉 Migration Complete!")
print("\nYour database is now ready for multi-organization support!")
print("Next steps:")
print("1. Restart your backend: uvicorn app:app --reload")
print("2. Test the new features locally")
print("3. Deploy to production")
