#!/usr/bin/env python3
"""
Database clearing utility script.
Run this to clear specific tables or all data from the database.
"""

import sys
from app import create_app, db
from app.models.user import User
from app.models.employee import Employee

def clear_all_data():
    """Clear all data from all tables."""
    print("🗑️  Clearing all data from database...")
    
    # Delete all records from each table
    Employee.query.delete()
    User.query.delete()
    
    db.session.commit()
    print("✅ All data cleared successfully!")

def clear_employees():
    """Clear only employee data."""
    print("🗑️  Clearing employee data...")
    Employee.query.delete()
    db.session.commit()
    print("✅ Employee data cleared successfully!")

def clear_users():
    """Clear only user data."""
    print("🗑️  Clearing user data...")
    User.query.delete()
    db.session.commit()
    print("✅ User data cleared successfully!")

def show_stats():
    """Show current database statistics."""
    users_count = User.query.count()
    employees_count = Employee.query.count()
    
    print(f"📊 Database Statistics:")
    print(f"   Users: {users_count}")
    print(f"   Employees: {employees_count}")

def main():
    """Main function with menu."""
    app = create_app()
    
    with app.app_context():
        if len(sys.argv) > 1:
            action = sys.argv[1].lower()
            
            if action == 'all':
                clear_all_data()
            elif action == 'employees':
                clear_employees()
            elif action == 'users':
                clear_users()
            elif action == 'stats':
                show_stats()
            else:
                print("❌ Invalid action. Use: all, employees, users, or stats")
                sys.exit(1)
        else:
            # Interactive menu
            print("\n🛠️  Database Clear Utility")
            print("1. Clear all data")
            print("2. Clear employees only")
            print("3. Clear users only")
            print("4. Show statistics")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                confirm = input("⚠️  Are you sure you want to clear ALL data? (yes/no): ")
                if confirm.lower() == 'yes':
                    clear_all_data()
                else:
                    print("❌ Operation cancelled")
            elif choice == '2':
                clear_employees()
            elif choice == '3':
                clear_users()
            elif choice == '4':
                show_stats()
            elif choice == '5':
                print("👋 Goodbye!")
            else:
                print("❌ Invalid choice")

if __name__ == '__main__':
    main() 