from fastapi import FastAPI, Depends, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Employee, WeeklyScore, User
from scoring import calculate_productivity
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import hashlib
import uuid

app = FastAPI(title="Employee Productivity Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://productivity-tracker-three.vercel.app",  # Replace with YOUR Vercel URL
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_session(user_id: int, organization_id: str, role: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        'user_id': user_id,
        'organization_id': organization_id,
        'role': role,
        'expires': datetime.now() + timedelta(days=7)
    }
    return token


def verify_session(token: str):
    if token not in sessions:
        return None
    session = sessions[token]
    if datetime.now() > session['expires']:
        del sessions[token]
        return None
    return session


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    session = verify_session(token)

    if not session:
        raise HTTPException(
            status_code=401, detail="Invalid or expired session")

    return session


# ============= AUTHENTICATION =============

@app.post("/auth/register")
def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400, detail="Username or email already exists")

    organization_id = str(uuid.uuid4())
    hashed_pw = hash_password(password)

    user = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        role="admin",
        organization_id=organization_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session(user.id, user.organization_id, user.role)

    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id
        }
    }


@app.post("/auth/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or user.password_hash != hash_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_session(user.id, user.organization_id, user.role)

    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id
        }
    }


@app.post("/auth/logout")
def logout(token: str = Form(...)):
    if token in sessions:
        del sessions[token]
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user['user_id']).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "organization_id": user.organization_id
    }


# ============= EMPLOYEE ENDPOINTS =============

@app.get("/")
def root():
    return {"status": "Backend running successfully"}


@app.get("/employees")
def get_employees(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Employee).filter(
        Employee.organization_id == current_user['organization_id']
    ).all()


@app.get("/employees/{employee_id}")
def get_employee(employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.organization_id == current_user['organization_id']
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@app.post("/employees")
def create_employee(
    name: str,
    department: str,
    role: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=403, detail="Only admins can create employees")

    employee = Employee(
        name=name,
        department=department,
        role=role,
        organization_id=current_user['organization_id']
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@app.put("/employees/{employee_id}")
def update_employee(
    employee_id: int,
    name: str = None,
    department: str = None,
    role: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=403, detail="Only admins can update employees")

    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.organization_id == current_user['organization_id']
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if name:
        employee.name = name
    if department:
        employee.department = department
    if role:
        employee.role = role

    db.commit()
    db.refresh(employee)
    return employee


@app.delete("/employees/{employee_id}")
def delete_employee(
    employee_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=403, detail="Only admins can delete employees")

    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.organization_id == current_user['organization_id']
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.query(WeeklyScore).filter(
        WeeklyScore.employee_id == employee_id).delete()
    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}


# ============= SCORE ENDPOINTS =============

@app.post("/scores")
def add_weekly_score(
    employee_id: int,
    week: str,
    task_completion: float,
    speed: float,
    professionalism: float,
    activity: float,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=403, detail="Only admins can add scores")

    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.organization_id == current_user['organization_id']
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    productivity = calculate_productivity(
        task_completion, speed, professionalism, activity
    )

    score = WeeklyScore(
        employee_id=employee_id,
        week=week,
        task_completion=task_completion,
        speed=speed,
        professionalism=professionalism,
        activity=activity,
        productivity_score=productivity,
        organization_id=current_user['organization_id']
    )

    db.add(score)
    db.commit()
    db.refresh(score)
    return score


@app.get("/scores")
def get_scores(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(WeeklyScore).filter(
        WeeklyScore.organization_id == current_user['organization_id']
    ).all()


@app.delete("/scores/{score_id}")
def delete_score(
    score_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=403, detail="Only admins can delete scores")

    score = db.query(WeeklyScore).filter(
        WeeklyScore.id == score_id,
        WeeklyScore.organization_id == current_user['organization_id']
    ).first()

    if not score:
        raise HTTPException(status_code=404, detail="Score not found")

    db.delete(score)
    db.commit()
    return {"message": "Score deleted successfully"}


# ============= TEAM MANAGEMENT ENDPOINTS =============

@app.get("/team/members")
def get_team_members(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=403, detail="Only admins can view team members")

    members = db.query(User).filter(
        User.organization_id == current_user['organization_id']
    ).all()

    return [
        {
            "id": member.id,
            "username": member.username,
            "email": member.email,
            "role": member.role,
            "created_at": member.created_at
        }
        for member in members
    ]


@app.post("/team/members")
def create_team_member(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("viewer"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=403, detail="Only admins can add team members")

    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400, detail="Username or email already exists")

    if role not in ['admin', 'viewer']:
        raise HTTPException(status_code=400, detail="Invalid role")

    hashed_pw = hash_password(password)
    new_member = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        role=role,
        organization_id=current_user['organization_id']
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return {
        "id": new_member.id,
        "username": new_member.username,
        "email": new_member.email,
        "role": new_member.role
    }


@app.delete("/team/members/{user_id}")
def delete_team_member(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=403, detail="Only admins can remove team members")

    if user_id == current_user['user_id']:
        raise HTTPException(
            status_code=400, detail="Cannot delete your own account")

    member = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user['organization_id']
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    db.delete(member)
    db.commit()

    return {"message": "Team member removed successfully"}


# ============= EXPORT ENDPOINTS =============

@app.get("/export/excel/{week}")
def export_to_excel(week: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    scores = db.query(WeeklyScore).filter(
        WeeklyScore.week == week,
        WeeklyScore.organization_id == current_user['organization_id']
    ).all()

    if not scores:
        raise HTTPException(
            status_code=404, detail=f"No scores found for week {week}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Week {week}"

    ws['A1'] = f'Weekly Productivity Report - {week}'
    ws['A1'].font = Font(size=16, bold=True)
    ws.merge_cells('A1:G1')

    headers = ['Employee ID', 'Employee Name', 'Task', 'Speed',
               'Professional', 'Activity', 'Productivity Score']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col)
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="4472C4",
                                end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')

    for row, score in enumerate(scores, start=4):
        employee = db.query(Employee).filter(
            Employee.id == score.employee_id).first()
        ws.cell(row=row, column=1).value = score.employee_id
        ws.cell(row=row, column=2).value = employee.name if employee else 'Unknown'
        ws.cell(row=row, column=3).value = score.task_completion
        ws.cell(row=row, column=4).value = score.speed
        ws.cell(row=row, column=5).value = score.professionalism
        ws.cell(row=row, column=6).value = score.activity
        ws.cell(row=row, column=7).value = score.productivity_score
        ws.cell(row=row, column=7).font = Font(bold=True)

    for col in range(1, 8):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=weekly_report_{week}.xlsx"}
    )


@app.get("/export/pdf/{week}")
def export_to_pdf(week: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    scores = db.query(WeeklyScore).filter(
        WeeklyScore.week == week,
        WeeklyScore.organization_id == current_user['organization_id']
    ).all()

    if not scores:
        raise HTTPException(
            status_code=404, detail=f"No scores found for week {week}")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph(
        f"<b>Weekly Productivity Report - {week}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))

    data = [['Employee', 'Task', 'Speed', 'Prof.', 'Activity', 'Score']]

    for score in scores:
        employee = db.query(Employee).filter(
            Employee.id == score.employee_id).first()
        data.append([
            employee.name if employee else 'Unknown',
            str(score.task_completion),
            str(score.speed),
            str(score.professionalism),
            str(score.activity),
            str(score.productivity_score)
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=weekly_report_{week}.pdf"}
    )


@app.post("/email/report")
def email_report(
    week: str = Form(...),
    recipient_email: str = Form(...),
    smtp_server: str = Form("smtp.gmail.com"),
    smtp_port: int = Form(587),
    sender_email: str = Form(...),
    sender_password: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        scores = db.query(WeeklyScore).filter(
            WeeklyScore.week == week,
            WeeklyScore.organization_id == current_user['organization_id']
        ).all()

        if not scores:
            raise HTTPException(
                status_code=404, detail=f"No scores for week {week}")

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f'Weekly Productivity Report - {week}'

        body = f"""
        <html>
        <body>
        <h2>Weekly Productivity Report - {week}</h2>
        <p>Please find the weekly productivity report attached.</p>
        <br>
        <table border="1" cellpadding="5">
        <tr style="background-color: #4472C4; color: white;">
            <th>Employee</th>
            <th>Task</th>
            <th>Speed</th>
            <th>Professional</th>
            <th>Activity</th>
            <th>Score</th>
        </tr>
        """

        for score in scores:
            employee = db.query(Employee).filter(
                Employee.id == score.employee_id).first()
            body += f"""
            <tr>
                <td>{employee.name if employee else 'Unknown'}</td>
                <td>{score.task_completion}</td>
                <td>{score.speed}</td>
                <td>{score.professionalism}</td>
                <td>{score.activity}</td>
                <td><b>{score.productivity_score}</b></td>
            </tr>
            """

        body += """
        </table>
        <br>
        <p>Best regards,<br>Productivity Tracker System</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        return {"message": f"Report emailed successfully to {recipient_email}"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error sending email: {str(e)}")
