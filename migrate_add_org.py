from sqlalchemy import text
from database import engine
import uuid

# Add organization_id columns to existing tables
with engine.connect() as conn:
    # Add to users table
    try:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'admin'"))
        conn.execute(
            text("ALTER TABLE users ADD COLUMN organization_id VARCHAR"))
        print("✅ Added columns to users table")
    except Exception as e:
        print(f"Users table: {e}")

    # Add to employees table
    try:
        conn.execute(
            text("ALTER TABLE employees ADD COLUMN organization_id VARCHAR"))
        print("✅ Added organization_id to employees table")
    except Exception as e:
        print(f"Employees table: {e}")

    # Add to weekly_scores table
    try:
        conn.execute(
            text("ALTER TABLE weekly_scores ADD COLUMN organization_id VARCHAR"))
        print("✅ Added organization_id to weekly_scores table")
    except Exception as e:
        print(f"Weekly_scores table: {e}")

    # Update existing users with a default organization_id
    try:
        default_org = str(uuid.uuid4())
        conn.execute(text(
            f"UPDATE users SET organization_id = '{default_org}' WHERE organization_id IS NULL"))
        conn.execute(text(
            f"UPDATE employees SET organization_id = '{default_org}' WHERE organization_id IS NULL"))
        conn.execute(text(
            f"UPDATE weekly_scores SET organization_id = '{default_org}' WHERE organization_id IS NULL"))
        print(f"✅ Updated existing data with organization_id: {default_org}")
    except Exception as e:
        print(f"Update error: {e}")

    conn.commit()

print("\n🎉 Migration complete!")
