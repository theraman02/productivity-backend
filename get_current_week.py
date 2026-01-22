from datetime import datetime

# Get current week in ISO format
current_week = datetime.now().strftime("%Y-W%W")
print(f"📅 Current week: {current_week}")
