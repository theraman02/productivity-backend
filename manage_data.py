from database import SessionLocal
from models import WeeklyScore, Employee
from datetime import datetime


def show_menu():
    print("\n" + "="*60)
    print("📊 DATA MANAGEMENT SYSTEM")
    print("="*60)
    print("1. View scores by week")
    print("2. Delete scores by week")
    print("3. Clear all scores (keep employees)")
    print("4. View weekly report")
    print("5. Get current week")
    print("6. Exit")
    print("="*60)


def view_scores_by_week(db):
    week = input("Enter week (or press Enter for all): ")
    if week:
        scores = db.query(WeeklyScore).filter(WeeklyScore.week == week).all()
    else:
        scores = db.query(WeeklyScore).all()

    if not scores:
        print("\n❌ No scores found.")
        return

    print(f"\n📊 SCORES:")
    print("-" * 80)
    for score in scores:
        emp = db.query(Employee).filter(
            Employee.id == score.employee_id).first()
        print(
            f"Week: {score.week} | Employee: {emp.name if emp else 'Unknown'} | Score: {score.productivity_score}")
    print("-" * 80)


def delete_week_scores(db):
    week = input("Enter week to delete: ")
    confirm = input(f"⚠️  Delete all scores from {week}? (yes/no): ")

    if confirm.lower() == 'yes':
        deleted = db.query(WeeklyScore).filter(
            WeeklyScore.week == week).delete()
        db.commit()
        print(f"✅ Deleted {deleted} scores from {week}")
    else:
        print("❌ Cancelled")


def clear_all_scores(db):
    confirm = input("⚠️  Delete ALL scores? Employees will remain. (yes/no): ")

    if confirm.lower() == 'yes':
        deleted = db.query(WeeklyScore).delete()
        db.commit()
        print(f"✅ Deleted {deleted} scores")
    else:
        print("❌ Cancelled")


def weekly_report(db):
    current_week = datetime.now().strftime("%Y-W%W")
    week = input(f"Week (Enter for current {current_week}): ") or current_week

    scores = db.query(WeeklyScore).filter(WeeklyScore.week == week).all()

    if not scores:
        print(f"\n❌ No scores for {week}")
        return

    print(f"\n📈 REPORT - {week}")
    print("=" * 60)

    for score in scores:
        emp = db.query(Employee).filter(
            Employee.id == score.employee_id).first()
        print(f"{emp.name if emp else 'Unknown'}: {score.productivity_score}")

    avg = sum(s.productivity_score for s in scores) / len(scores)
    print(f"\nAverage: {avg:.2f}")
    print("=" * 60)


def get_current_week():
    week = datetime.now().strftime("%Y-W%W")
    print(f"\n📅 Current week: {week}")


def main():
    db = SessionLocal()

    while True:
        show_menu()
        choice = input("\nChoice (1-6): ")

        if choice == '1':
            view_scores_by_week(db)
        elif choice == '2':
            delete_week_scores(db)
        elif choice == '3':
            clear_all_scores(db)
        elif choice == '4':
            weekly_report(db)
        elif choice == '5':
            get_current_week()
        elif choice == '6':
            print("\n👋 Goodbye!")
            db.close()
            break
        else:
            print("\n❌ Invalid choice")


if __name__ == "__main__":
    main()
