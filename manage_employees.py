from database import SessionLocal
from models import Employee


def show_menu():
    print("\n" + "="*50)
    print("🔧 EMPLOYEE MANAGEMENT SYSTEM")
    print("="*50)
    print("1. View all employees")
    print("2. Add new employee")
    print("3. Update employee")
    print("4. Delete employee")
    print("5. Exit")
    print("="*50)


def view_employees(db):
    employees = db.query(Employee).all()
    if not employees:
        print("\n❌ No employees found.")
        return

    print("\n📋 ALL EMPLOYEES:")
    print("-" * 80)
    print(f"{'ID':<5} {'Name':<25} {'Department':<20} {'Role':<30}")
    print("-" * 80)
    for emp in employees:
        print(f"{emp.id:<5} {emp.name:<25} {emp.department:<20} {emp.role:<30}")
    print("-" * 80)


def add_employee(db):
    print("\n➕ ADD NEW EMPLOYEE")
    name = input("Enter name: ")
    department = input("Enter department: ")
    role = input("Enter role: ")

    employee = Employee(name=name, department=department, role=role)
    db.add(employee)
    db.commit()
    print(f"\n✅ Employee '{name}' added successfully!")


def update_employee(db):
    view_employees(db)
    emp_id = int(input("\n🔄 Enter employee ID to update: "))

    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        print(f"\n❌ Employee with ID {emp_id} not found.")
        return

    print(
        f"\nCurrent details: {employee.name} | {employee.department} | {employee.role}")
    print("(Press Enter to keep current value)")

    name = input(f"New name [{employee.name}]: ") or employee.name
    department = input(
        f"New department [{employee.department}]: ") or employee.department
    role = input(f"New role [{employee.role}]: ") or employee.role

    employee.name = name
    employee.department = department
    employee.role = role
    db.commit()
    print(f"\n✅ Employee updated successfully!")


def delete_employee(db):
    view_employees(db)
    emp_id = int(input("\n🗑️  Enter employee ID to delete: "))

    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        print(f"\n❌ Employee with ID {emp_id} not found.")
        return

    confirm = input(
        f"⚠️  Are you sure you want to delete '{employee.name}'? (yes/no): ")
    if confirm.lower() == 'yes':
        db.delete(employee)
        db.commit()
        print(f"\n✅ Employee '{employee.name}' deleted successfully!")
    else:
        print("\n❌ Deletion cancelled.")


def main():
    db = SessionLocal()

    while True:
        show_menu()
        choice = input("\nEnter your choice (1-5): ")

        if choice == '1':
            view_employees(db)
        elif choice == '2':
            add_employee(db)
        elif choice == '3':
            update_employee(db)
        elif choice == '4':
            delete_employee(db)
        elif choice == '5':
            print("\n👋 Goodbye!")
            db.close()
            break
        else:
            print("\n❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
