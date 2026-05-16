from backend.database.config import SessionLocal, engine, Base
from backend.database import models
from backend.security.auth import get_password_hash

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Create Roles
    roles = ["ADMIN", "HR", "FINANCE", "ENGINEERING", "DEVOPS", "SECURITY", "AUDITOR"]
    for role_name in roles:
        if not db.query(models.Role).filter(models.Role.name == role_name).first():
            db.add(models.Role(name=role_name))
    db.commit()

    # Create Users
    users_data = [
        {"username": "admin_user", "password": "password123", "role": "ADMIN", "department": "Management"},
        {"username": "hr_user", "password": "password123", "role": "HR", "department": "HR"},
        {"username": "finance_user", "password": "password123", "role": "FINANCE", "department": "Finance"},
        {"username": "eng_user", "password": "password123", "role": "ENGINEERING", "department": "Engineering"},
        {"username": "sec_user", "password": "password123", "role": "SECURITY", "department": "Security"},
    ]

    for ud in users_data:
        if not db.query(models.User).filter(models.User.username == ud["username"]).first():
            role = db.query(models.Role).filter(models.Role.name == ud["role"]).first()
            user = models.User(
                username=ud["username"],
                password_hash=get_password_hash(ud["password"]),
                role_id=role.id,
                department=ud["department"]
            )
            db.add(user)
    db.commit()

    # Synthetic Employees
    employees = [
        {"name": "Alice Smith", "department": "HR", "role": "HR Manager", "salary": 95000, "performance_rating": "Exceeds Expectations"},
        {"name": "Bob Jones", "department": "Engineering", "role": "Senior Engineer", "salary": 145000, "performance_rating": "Meets Expectations"},
        {"name": "Charlie Brown", "department": "Finance", "role": "Analyst", "salary": 85000, "performance_rating": "Needs Improvement"},
    ]
    for emp in employees:
        if not db.query(models.EmployeeRecord).filter(models.EmployeeRecord.name == emp["name"]).first():
            db.add(models.EmployeeRecord(**emp))
    
    # Synthetic Financials
    financials = [
        {"quarter": "Q1", "year": 2026, "revenue": 5000000, "expenses": 3000000, "status": "FINAL"},
        {"quarter": "Q2", "year": 2026, "revenue": 5500000, "expenses": 3200000, "status": "FINAL"},
        {"quarter": "Q3", "year": 2026, "revenue": 6000000, "expenses": 4000000, "status": "DRAFT"},
    ]
    for fin in financials:
        if not db.query(models.FinancialReport).filter(models.FinancialReport.quarter == fin["quarter"], models.FinancialReport.year == fin["year"]).first():
            db.add(models.FinancialReport(**fin))
            
    db.commit()
    db.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
