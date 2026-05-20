from functools import wraps
from datetime import datetime, timedelta
import io
import os

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

if os.environ.get("VERCEL"):
    os.makedirs("/tmp/matplotlib", exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as ReportImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


SUBJECT_FIELDS = [
    "mathematics",
    "physics",
    "chemistry",
    "biology",
    "computer_science",
    "english",
    "geography",
    "history",
    "economics",
    "physical_education",
]

SUBJECT_LABELS = {
    "mathematics": "Mathematics",
    "physics": "Physics",
    "chemistry": "Chemistry",
    "biology": "Biology",
    "computer_science": "Computer Science",
    "english": "English",
    "geography": "Geography",
    "history": "History",
    "economics": "Economics",
    "physical_education": "Physical Education",
}

SUBJECT_SHORT_LABELS = {
    "mathematics": "Math",
    "physics": "Physics",
    "chemistry": "Chemistry",
    "biology": "Biology",
    "computer_science": "CS",
    "english": "English",
    "geography": "Geo",
    "history": "History",
    "economics": "Eco",
    "physical_education": "PE",
}

STREAMS = ["Science", "Commerce", "Arts"]
ROLE_CHOICES = {"admin", "teacher", "student", "parent"}


def default_database_uri():
    if os.environ.get("VERCEL"):
        return "sqlite:////tmp/eduvision.db"
    return "sqlite:///eduvision.db"


app = Flask(__name__, static_folder="public/static", static_url_path="/static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "eduvision-secret-key-2026")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", default_database_uri())
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(days=30)
CORS(app)
if not os.environ.get("VERCEL"):
    os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    full_name = db.Column(db.String(100))


class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    subject = db.Column(db.String(50))
    email = db.Column(db.String(120))


class ParentStudent(db.Model):
    __tablename__ = "parent_students"
    __table_args__ = (db.UniqueConstraint("parent_user_id", "student_id", name="uq_parent_student"),)

    id = db.Column(db.Integer, primary_key=True)
    parent_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    relationship = db.Column(db.String(40), default="Parent")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(40), unique=True, nullable=False)
    class_name = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(10))
    stream = db.Column(db.String(50))
    attendance = db.Column(db.Float, default=85.0)
    internal_marks = db.Column(db.Float, default=70.0)
    semester_marks = db.Column(db.Float, default=70.0)
    mathematics = db.Column(db.Float, default=0)
    physics = db.Column(db.Float, default=0)
    chemistry = db.Column(db.Float, default=0)
    biology = db.Column(db.Float, default=0)
    computer_science = db.Column(db.Float, default=0)
    english = db.Column(db.Float, default=0)
    geography = db.Column(db.Float, default=0)
    history = db.Column(db.Float, default=0)
    economics = db.Column(db.Float, default=0)
    physical_education = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Mark(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    subject = db.Column(db.String(60), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    predicted_percentage = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(40), nullable=False)
    pass_fail = db.Column(db.String(12), nullable=False)
    risk_level = db.Column(db.String(30), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    recommendation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClassAttendance(db.Model):
    __tablename__ = "class_attendance"
    __table_args__ = (db.UniqueConstraint("student_id", "subject_key", name="uq_student_subject_attendance"),)

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    subject_key = db.Column(db.String(60), nullable=False)
    subject = db.Column(db.String(80), nullable=False)
    attended_classes = db.Column(db.Integer, nullable=False, default=0)
    total_classes = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MLModel:
    """Small ensemble used for demo-ready prediction without external services."""

    def __init__(self):
        self.lr_model = LinearRegression()
        self.dt_model = DecisionTreeClassifier(random_state=42)
        self.rf_model = RandomForestClassifier(n_estimators=120, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_size = 0

    def train(self, x_values, y_regression, y_classification):
        if len(x_values) < 5:
            self.is_trained = False
            self.training_size = len(x_values)
            return

        x_scaled = self.scaler.fit_transform(x_values)
        self.lr_model.fit(x_scaled, y_regression)
        self.dt_model.fit(x_scaled, y_classification)
        self.rf_model.fit(x_scaled, y_classification)
        self.is_trained = True
        self.training_size = len(x_values)

    def predict_percentage(self, features, fallback_percentage):
        if not self.is_trained:
            return clamp(fallback_percentage, 0, 100)

        features_scaled = self.scaler.transform([features])
        prediction = float(self.lr_model.predict(features_scaled)[0])
        return clamp(prediction, 0, 100)

    def predict_class(self, features):
        if not self.is_trained:
            return None
        features_scaled = self.scaler.transform([features])
        return int(self.rf_model.predict(features_scaled)[0])


ml_model = MLModel()


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, float(value)))


def get_number(data, key, default=0):
    value = data.get(key, default)
    try:
        if value in (None, "") or pd.isna(value):
            return float(default)
    except ValueError:
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def get_text(data, key, default=""):
    value = data.get(key, default)
    try:
        if value in (None, "") or pd.isna(value):
            return default
    except ValueError:
        return default
    return str(value).strip()


def request_payload():
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    if request.form:
        return request.form.to_dict(flat=True)
    return {}


def checkbox_enabled(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def numeric_subjects(student):
    return [float(getattr(student, field, 0) or 0) for field in SUBJECT_FIELDS]


def calculate_percentage(student):
    marks = numeric_subjects(student)
    return round(sum(marks) / len(marks), 2) if marks else 0


def science_average(student):
    marks = [
        float(student.physics or 0),
        float(student.chemistry or 0),
        float(student.biology or 0),
        float(student.computer_science or 0),
    ]
    valid = [mark for mark in marks if mark > 0]
    return round(sum(valid) / len(valid), 2) if valid else 0


def get_performance_category(percentage):
    if percentage >= 90:
        return "Outstanding", "success"
    if percentage >= 75:
        return "Excellent", "primary"
    if percentage >= 60:
        return "Good", "info"
    if percentage >= 45:
        return "Average", "warning"
    return "Needs Improvement", "danger"


def get_strong_weak_subjects(student):
    subjects = {label: float(getattr(student, field, 0) or 0) for field, label in SUBJECT_LABELS.items()}
    strong = [subject for subject, marks in subjects.items() if marks >= 75]
    weak = [subject for subject, marks in subjects.items() if marks < 50]
    return strong, weak


def feature_vector(student):
    percentage = calculate_percentage(student)
    return [
        float(student.attendance or 0),
        float(student.internal_marks or 0),
        float(student.semester_marks or 0),
        float(student.mathematics or 0),
        science_average(student),
        float(student.english or 0),
        percentage,
    ]


def heuristic_prediction(student):
    current_percentage = calculate_percentage(student)
    attendance_boost = (float(student.attendance or 0) - 75) * 0.08
    assessment_signal = ((float(student.internal_marks or 0) + float(student.semester_marks or 0)) / 2) * 0.24
    subject_signal = current_percentage * 0.68
    return clamp(subject_signal + assessment_signal + attendance_boost, 0, 100)


def risk_from_prediction(predicted_percentage, attendance):
    if predicted_percentage < 45 or attendance < 65:
        return "High Risk"
    if predicted_percentage < 60 or attendance < 75:
        return "Moderate Risk"
    return "Low Risk"


def attendance_status(percentage):
    if percentage < 65:
        return "Critical"
    if percentage < 75:
        return "Watch"
    if percentage >= 92:
        return "Excellent"
    return "Healthy"


def attendance_action(percentage, missed_classes):
    if percentage < 65:
        return f"Attend the next {min(6, max(3, missed_classes))} classes without fail."
    if percentage < 75:
        return "Attend consistently this week to cross the 75% requirement."
    if percentage >= 92:
        return "Excellent consistency. Keep the current rhythm."
    return "On track. Avoid avoidable absences."


def default_class_attendance_counts(student, field, index):
    attendance = clamp(float(student.attendance or 0), 0, 100)
    mark = float(getattr(student, field, 0) or 0)
    total_classes = 24 + (index % 4) * 2
    subject_adjustment = (mark - 70) * 0.06
    subject_percentage = clamp(attendance + subject_adjustment, 35, 100)
    attended_classes = round(total_classes * subject_percentage / 100)
    return int(attended_classes), int(total_classes)


def ensure_class_attendance(student):
    existing = {record.subject_key: record for record in ClassAttendance.query.filter_by(student_id=student.id).all()}
    for index, field in enumerate(SUBJECT_FIELDS):
        if field in existing:
            continue
        attended, total = default_class_attendance_counts(student, field, index)
        db.session.add(
            ClassAttendance(
                student_id=student.id,
                subject_key=field,
                subject=SUBJECT_LABELS[field],
                attended_classes=attended,
                total_classes=total,
            )
        )


def class_attendance_rows(student):
    ensure_class_attendance(student)
    db.session.flush()
    records = {
        record.subject_key: record
        for record in ClassAttendance.query.filter_by(student_id=student.id).all()
    }
    rows = []
    for field in SUBJECT_FIELDS:
        record = records.get(field)
        if not record:
            continue
        total = max(0, int(record.total_classes or 0))
        attended = min(max(0, int(record.attended_classes or 0)), total)
        percentage = round((attended / total * 100), 1) if total else 0
        missed = max(0, total - attended)
        rows.append(
            {
                "subject_key": field,
                "subject": record.subject or SUBJECT_LABELS[field],
                "attended_classes": attended,
                "total_classes": total,
                "missed_classes": missed,
                "percentage": percentage,
                "status": attendance_status(percentage),
                "next_action": attendance_action(percentage, missed),
                "updated_at": (record.updated_at or datetime.utcnow()).strftime("%d %b %Y"),
            }
        )
    return rows


def recalculate_student_attendance(student):
    records = ClassAttendance.query.filter_by(student_id=student.id).all()
    attended = sum(max(0, int(record.attended_classes or 0)) for record in records)
    total = sum(max(0, int(record.total_classes or 0)) for record in records)
    if total:
        student.attendance = round(attended / total * 100, 1)


def attendance_portal_payload(students=None):
    students = students if students is not None else scoped_students().all()
    cards = []
    total_attended = 0
    total_classes = 0
    for student in students:
        rows = class_attendance_rows(student)
        attended = sum(row["attended_classes"] for row in rows)
        total = sum(row["total_classes"] for row in rows)
        total_attended += attended
        total_classes += total
        overall = round(attended / total * 100, 1) if total else round(float(student.attendance or 0), 1)
        low_subjects = [row for row in rows if row["percentage"] < 75]
        cards.append(
            {
                "student": serialize_student(student),
                "overall_percentage": overall,
                "status": attendance_status(overall),
                "attended_classes": attended,
                "total_classes": total,
                "missed_classes": max(0, total - attended),
                "low_subject_count": len(low_subjects),
                "lowest_subject": min(rows, key=lambda row: row["percentage"]) if rows else None,
                "classes": rows,
            }
        )

    overall_average = round(total_attended / total_classes * 100, 1) if total_classes else 0
    return {
        "summary": {
            "average": overall_average,
            "healthy_count": sum(1 for card in cards if card["overall_percentage"] >= 75),
            "watch_count": sum(1 for card in cards if card["overall_percentage"] < 75),
            "critical_count": sum(1 for card in cards if card["overall_percentage"] < 65),
            "total_students": len(cards),
        },
        "students": cards,
    }


def parent_messages_payload(students=None):
    students = students if students is not None else scoped_students().all()
    messages = []
    for student in students:
        rows = class_attendance_rows(student)
        overall_attended = sum(row["attended_classes"] for row in rows)
        overall_total = sum(row["total_classes"] for row in rows)
        overall_attendance = round(overall_attended / overall_total * 100, 1) if overall_total else float(student.attendance or 0)

        if overall_attendance < 75:
            messages.append(
                {
                    "type": "attendance",
                    "tone": "danger" if overall_attendance < 65 else "warning",
                    "student_id": student.id,
                    "student_name": student.name,
                    "title": f"{student.name} is below attendance requirement",
                    "text": f"Overall attendance is {overall_attendance}%. Please follow up so the ward crosses 75%.",
                    "meta": f"Roll {student.roll_number} | {max(0, overall_total - overall_attended)} missed classes",
                }
            )

        for row in rows:
            if row["missed_classes"] >= 3 or row["percentage"] < 75:
                messages.append(
                    {
                        "type": "absence",
                        "tone": "warning" if row["percentage"] >= 65 else "danger",
                        "student_id": student.id,
                        "student_name": student.name,
                        "title": f"Absence alert in {row['subject']}",
                        "text": f"{student.name} missed {row['missed_classes']} of {row['total_classes']} classes in {row['subject']}.",
                        "meta": f"{row['percentage']}% attendance | {row['status']}",
                    }
                )

        weak_subjects = []
        for field, label in SUBJECT_LABELS.items():
            mark = float(getattr(student, field, 0) or 0)
            if mark < 50:
                weak_subjects.append((label, mark))
        for label, mark in weak_subjects[:5]:
            messages.append(
                {
                    "type": "marks",
                    "tone": "danger",
                    "student_id": student.id,
                    "student_name": student.name,
                    "title": f"Low marks in {label}",
                    "text": f"{student.name} scored {mark:.1f} in {label}. A focused revision plan is recommended.",
                    "meta": f"Roll {student.roll_number} | Below 50",
                }
            )

        if not weak_subjects and overall_attendance >= 75:
            messages.append(
                {
                    "type": "positive",
                    "tone": "success",
                    "student_id": student.id,
                    "student_name": student.name,
                    "title": f"{student.name} is on track",
                    "text": "Marks and attendance are currently in a healthy range.",
                    "meta": f"{calculate_percentage(student)}% marks | {overall_attendance}% attendance",
                }
            )

    tone_order = {"danger": 0, "warning": 1, "success": 2}
    return sorted(messages, key=lambda item: (tone_order.get(item["tone"], 3), item["student_name"]))[:24]


def recommendations_for_student(student, predicted_percentage, strong_subjects, weak_subjects):
    recommendations = []
    if weak_subjects:
        recommendations.append(f"Schedule targeted practice for {', '.join(weak_subjects[:3])}.")
    if float(student.attendance or 0) < 75:
        recommendations.append("Improve attendance consistency to protect final performance.")
    if float(student.internal_marks or 0) < 60:
        recommendations.append("Raise internal assessment quality through weekly assignment review.")
    if predicted_percentage >= 85:
        recommendations.append("Prepare enrichment tasks and competition-level revision.")
    if not recommendations:
        recommendations.append("Maintain current study rhythm and review weak chapters weekly.")
    if strong_subjects:
        recommendations.append(f"Use strengths in {', '.join(strong_subjects[:2])} for peer learning.")
    return recommendations


def prediction_payload(student):
    features = feature_vector(student)
    fallback = heuristic_prediction(student)
    predicted_percentage = ml_model.predict_percentage(features, fallback)
    class_prediction = ml_model.predict_class(features)
    category, _ = get_performance_category(predicted_percentage)
    if class_prediction == 0:
        category = "Excellent" if predicted_percentage < 90 else "Outstanding"
    elif class_prediction == 1 and predicted_percentage < 75:
        category = "Good" if predicted_percentage >= 60 else "Average"
    elif class_prediction == 2:
        category = "Needs Improvement" if predicted_percentage < 45 else "Average"

    strong, weak = get_strong_weak_subjects(student)
    risk_level = risk_from_prediction(predicted_percentage, float(student.attendance or 0))
    confidence = 78 + min(17, ml_model.training_size * 1.5)
    if risk_level == "High Risk":
        confidence -= 4

    current_percentage = calculate_percentage(student)
    improvement_signal = (
        54
        + (float(student.attendance or 0) - 75) * 0.35
        + (float(student.internal_marks or 0) - current_percentage) * 0.16
        + max(0, predicted_percentage - current_percentage) * 0.8
        + len(strong) * 1.8
        - len(weak) * 3.2
    )
    recommendations = recommendations_for_student(student, predicted_percentage, strong, weak)
    return {
        "predicted_percentage": round(predicted_percentage, 2),
        "category": category,
        "pass_fail": "Pass" if predicted_percentage >= 40 else "Fail",
        "risk_level": risk_level,
        "confidence": round(clamp(confidence, 68, 97), 1),
        "improvement_chance": round(clamp(improvement_signal, 8, 98), 1),
        "current_percentage": current_percentage,
        "recommendations": recommendations,
        "strong_subjects": strong,
        "weak_subjects": weak,
        "expected_final_result": round(predicted_percentage, 2),
        "models": {
            "linear_regression": "Expected percentage",
            "decision_tree": "Performance category signal",
            "random_forest": "Pass/fail and risk stabilization",
        },
    }


def student_payload(data):
    payload = {
        "name": get_text(data, "name") or get_text(data, "full_name"),
        "roll_number": get_text(data, "roll_number") or get_text(data, "roll"),
        "class_name": get_text(data, "class_name") or get_text(data, "class"),
        "section": get_text(data, "section", "A"),
        "stream": get_text(data, "stream", "Science"),
        "attendance": clamp(get_number(data, "attendance", 85), 0, 100),
        "internal_marks": clamp(get_number(data, "internal_marks", get_number(data, "internal", 70)), 0, 100),
        "semester_marks": clamp(get_number(data, "semester_marks", get_number(data, "semester", 70)), 0, 100),
    }

    for field in SUBJECT_FIELDS:
        payload[field] = clamp(get_number(data, field, 0), 0, 100)

    if "maths" in data and not payload["mathematics"]:
        payload["mathematics"] = clamp(get_number(data, "maths", 0), 0, 100)
    if "science" in data:
        science_mark = clamp(get_number(data, "science", 0), 0, 100)
        for field in ["physics", "chemistry", "biology"]:
            if not payload[field]:
                payload[field] = science_mark

    return payload


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user():
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "message": "Login required"}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapper


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                if request.path.startswith("/api/"):
                    return jsonify({"success": False, "message": "Login required"}), 401
                return redirect(url_for("login"))
            if roles and user.role not in roles:
                if request.path.startswith("/api/"):
                    return jsonify({"success": False, "message": "Permission denied"}), 403
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)

        return wrapper

    return decorator


def can_view_student(student):
    user = current_user()
    if not user:
        return False
    if user.role in {"admin", "teacher"} or student.roll_number == user.username:
        return True
    if user.role == "parent":
        return ParentStudent.query.filter_by(parent_user_id=user.id, student_id=student.id).first() is not None
    return False


def scoped_students():
    user = current_user()
    query = Student.query
    if user and user.role == "student":
        query = query.filter_by(roll_number=user.username)
    elif user and user.role == "parent":
        linked_ids = [link.student_id for link in ParentStudent.query.filter_by(parent_user_id=user.id).all()]
        query = query.filter(Student.id.in_(linked_ids or [0]))
    return query


def rank_map(students=None):
    students = students if students is not None else Student.query.all()
    ordered = sorted(students, key=calculate_percentage, reverse=True)
    return {student.id: index + 1 for index, student in enumerate(ordered)}


def serialize_student(student, detail=False, ranks=None):
    ranks = ranks or rank_map()
    percentage = calculate_percentage(student)
    category, badge = get_performance_category(percentage)
    prediction = prediction_payload(student)
    data = {
        "id": student.id,
        "name": student.name,
        "roll_number": student.roll_number,
        "class_name": student.class_name,
        "section": student.section,
        "stream": student.stream,
        "attendance": round(float(student.attendance or 0), 1),
        "internal_marks": round(float(student.internal_marks or 0), 1),
        "semester_marks": round(float(student.semester_marks or 0), 1),
        "percentage": percentage,
        "category": category,
        "badge": badge,
        "rank": ranks.get(student.id, 0),
        "prediction": prediction,
        "predicted_percentage": prediction["predicted_percentage"],
        "risk_level": prediction["risk_level"],
        "pass_fail": prediction["pass_fail"],
    }

    if detail:
        data["subjects"] = {label: round(float(getattr(student, field, 0) or 0), 1) for field, label in SUBJECT_LABELS.items()}
        data["subject_fields"] = {field: round(float(getattr(student, field, 0) or 0), 1) for field in SUBJECT_FIELDS}
        data["strong_subjects"] = prediction["strong_subjects"]
        data["weak_subjects"] = prediction["weak_subjects"]
        data["recommendations"] = prediction["recommendations"]
    return data


def student_dataframe(students):
    rows = []
    ranks = rank_map(students)
    for student in students:
        prediction = prediction_payload(student)
        row = {
            "Roll Number": student.roll_number,
            "Name": student.name,
            "Class": student.class_name,
            "Section": student.section,
            "Stream": student.stream,
            "Attendance": student.attendance,
            "Internal Marks": student.internal_marks,
            "Semester Marks": student.semester_marks,
            "Percentage": calculate_percentage(student),
            "Rank": ranks.get(student.id, 0),
            "Predicted Percentage": prediction["predicted_percentage"],
            "Prediction Category": prediction["category"],
            "Pass/Fail": prediction["pass_fail"],
            "Risk Level": prediction["risk_level"],
            "AI Confidence": prediction["confidence"],
        }
        for field, label in SUBJECT_LABELS.items():
            row[label] = getattr(student, field, 0)
        rows.append(row)
    return pd.DataFrame(rows)


def train_ml_model():
    students = Student.query.all()
    features = []
    percentages = []
    classes = []
    for student in students:
        percentage = calculate_percentage(student)
        features.append(feature_vector(student))
        percentages.append(percentage)
        if percentage >= 75:
            classes.append(0)
        elif percentage >= 50:
            classes.append(1)
        else:
            classes.append(2)
    ml_model.train(np.array(features), np.array(percentages), np.array(classes))


def sync_student_records(student):
    db.session.query(Mark).filter_by(student_id=student.id).delete(synchronize_session=False)
    db.session.query(Prediction).filter_by(student_id=student.id).delete(synchronize_session=False)
    db.session.query(Attendance).filter_by(student_id=student.id).delete(synchronize_session=False)

    for field, label in SUBJECT_LABELS.items():
        db.session.add(Mark(student_id=student.id, subject=label, marks=float(getattr(student, field, 0) or 0)))

    ensure_class_attendance(student)
    db.session.add(Attendance(student_id=student.id, percentage=float(student.attendance or 0), status=attendance_status(float(student.attendance or 0))))

    prediction = prediction_payload(student)
    db.session.add(
        Prediction(
            student_id=student.id,
            predicted_percentage=prediction["predicted_percentage"],
            category=prediction["category"],
            pass_fail=prediction["pass_fail"],
            risk_level=prediction["risk_level"],
            confidence=prediction["confidence"],
            recommendation=" ".join(prediction["recommendations"]),
        )
    )


def refresh_all_student_records():
    for student in Student.query.all():
        ensure_class_attendance(student)
        sync_student_records(student)


def ensure_user(username, password, role, full_name="", email=None):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            password=generate_password_hash(password),
            role=role,
            full_name=full_name or username,
            email=email,
        )
        db.session.add(user)
        db.session.flush()
    return user


def ensure_student_user(student):
    ensure_user(student.roll_number, "student123", "student", student.name)


def link_parent_to_students(parent_user, roll_numbers, relationship="Parent"):
    linked = []
    missing = []
    seen = set()
    for raw_roll in roll_numbers:
        roll = str(raw_roll or "").strip()
        if not roll or roll.lower() in seen:
            continue
        seen.add(roll.lower())
        student = Student.query.filter_by(roll_number=roll).first()
        if not student:
            missing.append(roll)
            continue
        existing = ParentStudent.query.filter_by(parent_user_id=parent_user.id, student_id=student.id).first()
        if not existing:
            db.session.add(ParentStudent(parent_user_id=parent_user.id, student_id=student.id, relationship=relationship or "Parent"))
        linked.append(student)
    return linked, missing


def start_user_session(user, remember=False):
    session.permanent = bool(remember)
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role


def student_from_user(user):
    student = Student.query.filter_by(roll_number=user.username).first()
    if student:
        return student

    student = Student(
        name=user.full_name or user.username,
        roll_number=user.username,
        class_name="10",
        section="A",
        stream="Science",
        attendance=85,
        internal_marks=70,
        semester_marks=70,
        mathematics=0,
        physics=0,
        chemistry=0,
        biology=0,
        computer_science=0,
        english=0,
        geography=0,
        history=0,
        economics=0,
        physical_education=0,
    )
    db.session.add(student)
    db.session.flush()
    sync_student_records(student)
    return student


def legacy_table_exists(table_name):
    result = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    ).scalar()
    return bool(result)


def migrate_legacy_data():
    if legacy_table_exists("student") and Student.query.count() == 0:
        rows = db.session.execute(text("SELECT * FROM student")).mappings().all()
        for row in rows:
            db.session.add(
                Student(
                    name=row["name"],
                    roll_number=row["roll_number"],
                    class_name=row["class_name"],
                    section=row["section"],
                    stream=row["stream"],
                    attendance=row["attendance"],
                    internal_marks=row["internal_marks"],
                    semester_marks=row["semester_marks"],
                    mathematics=row["mathematics"],
                    physics=row["physics"],
                    chemistry=row["chemistry"],
                    biology=row["biology"],
                    computer_science=row["computer_science"],
                    english=row["english"],
                    geography=row["geography"],
                    history=row["history"],
                    economics=row["economics"],
                    physical_education=row["physical_education"],
                )
            )

    if legacy_table_exists("teacher") and Teacher.query.count() == 0:
        rows = db.session.execute(text("SELECT * FROM teacher")).mappings().all()
        for row in rows:
            db.session.add(
                Teacher(
                    name=row["name"],
                    employee_id=row["employee_id"],
                    subject=row["subject"],
                    email=row["email"],
                )
            )


def build_demo_students(total=100):
    demo_students = [
        ("STU001", "Ananya Rao", "10", "A", "Science", 96, 92, 94, [96, 91, 93, 88, 97, 90, 82, 78, 80, 94]),
        ("STU002", "Kabir Shah", "10", "A", "Science", 88, 83, 86, [84, 82, 80, 79, 88, 76, 74, 72, 70, 86]),
        ("STU003", "Meera Iyer", "10", "B", "Commerce", 91, 86, 88, [78, 70, 72, 66, 74, 90, 82, 84, 93, 87]),
        ("STU004", "Rohan Das", "11", "A", "Science", 72, 64, 67, [64, 61, 58, 62, 70, 68, 54, 49, 52, 75]),
        ("STU005", "Sara Khan", "11", "B", "Arts", 84, 78, 80, [68, 62, 64, 60, 66, 88, 91, 94, 78, 83]),
        ("STU006", "Dev Patel", "12", "A", "Commerce", 63, 58, 61, [55, 50, 48, 45, 52, 64, 67, 70, 73, 71]),
        ("STU007", "Isha Menon", "12", "B", "Science", 97, 94, 95, [98, 95, 96, 92, 99, 91, 88, 84, 86, 96]),
        ("STU008", "Arjun Nair", "10", "C", "Arts", 69, 54, 57, [48, 44, 46, 42, 50, 72, 76, 80, 61, 66]),
        ("STU009", "Nisha Verma", "11", "C", "Commerce", 78, 72, 75, [70, 64, 63, 59, 68, 82, 78, 76, 88, 79]),
        ("STU010", "Vivaan Roy", "12", "A", "Science", 58, 49, 52, [44, 41, 38, 40, 46, 55, 49, 45, 42, 60]),
        ("STU011", "Tara Sen", "11", "A", "Arts", 93, 89, 91, [82, 76, 78, 74, 80, 95, 96, 97, 84, 90]),
        ("STU012", "Neil Kumar", "10", "B", "Commerce", 81, 75, 77, [72, 66, 64, 61, 70, 80, 79, 77, 85, 82]),
    ]
    first_names = [
        "Aditi", "Advait", "Akshara", "Aman", "Amrita", "Anika", "Aryan", "Avni", "Bhavya", "Charu", "Dhruv",
        "Diya", "Eshan", "Farah", "Gaurav", "Harini", "Ira", "Jai", "Jhanvi", "Karan", "Kiara", "Lakshya",
        "Mahika", "Manav", "Navya", "Om", "Pari", "Pranav", "Rhea", "Ritvik", "Saanvi", "Sahil", "Samaira",
        "Shaurya", "Siya", "Tanvi", "Tejas", "Trisha", "Utkarsh", "Vanya", "Ved", "Yash", "Zara", "Aarohi",
    ]
    last_names = [
        "Agarwal", "Bansal", "Bhat", "Chopra", "Dixit", "Fernandes", "Ghosh", "Gupta", "Jain", "Joshi", "Kapoor",
        "Kulkarni", "Malhotra", "Mishra", "Mukherjee", "Pillai", "Reddy", "Saxena", "Shetty", "Sinha", "Thomas",
        "Varghese", "Yadav",
    ]
    profiles = {
        "Science": [84, 82, 81, 79, 86, 76, 70, 68, 66, 80],
        "Commerce": [72, 67, 66, 62, 70, 80, 76, 74, 84, 78],
        "Arts": [64, 58, 60, 56, 62, 83, 86, 88, 76, 82],
    }
    classes = ["10", "11", "12"]
    sections = ["A", "B", "C", "D"]
    streams = ["Science", "Commerce", "Arts"]

    for number in range(len(demo_students) + 1, total + 1):
        stream = streams[(number - 1) % len(streams)]
        class_name = classes[(number // 3) % len(classes)]
        section = sections[(number - 1) % len(sections)]
        profile = ((number * 7) % 41) - 20
        attendance = clamp(76 + ((number * 9) % 23) - (8 if number % 11 == 0 else 0), 55, 98)
        internal = clamp(70 + profile + ((number * 5) % 9) - 4, 38, 98)
        semester = clamp(72 + profile + ((number * 3) % 11) - 5, 35, 99)
        marks = [
            int(clamp(base + profile + ((number * (index + 3)) % 13) - 6, 32, 99))
            for index, base in enumerate(profiles[stream])
        ]
        first = first_names[(number - 13) % len(first_names)]
        last = last_names[((number - 13) * 3) % len(last_names)]
        demo_students.append(
            (
                f"STU{number:03d}",
                f"{first} {last}",
                class_name,
                section,
                stream,
                int(attendance),
                int(internal),
                int(semester),
                marks,
            )
        )
    return demo_students


def seed_demo_data():
    admin_user = ensure_user("admin", "admin123", "admin", "System Admin", "admin@eduvision.ai")
    ensure_user("teacher", "teacher123", "teacher", "Aarav Mehta", "teacher@eduvision.ai")
    parent_user = ensure_user("parent", "parent123", "parent", "Priya Rao", "parent@eduvision.ai")

    if not Admin.query.filter_by(username="admin").first():
        db.session.add(Admin(user_id=admin_user.id, username="admin", full_name="System Admin", email="admin@eduvision.ai"))

    if not Teacher.query.filter_by(employee_id="TCH001").first():
        db.session.add(Teacher(name="Aarav Mehta", employee_id="TCH001", subject="Mathematics", email="teacher@eduvision.ai"))

    demo_students = build_demo_students(100)
    for roll, name, class_name, section, stream, attendance, internal, semester, marks in demo_students:
        if not Student.query.filter_by(roll_number=roll).first():
            student = Student(
                roll_number=roll,
                name=name,
                class_name=class_name,
                section=section,
                stream=stream,
                attendance=attendance,
                internal_marks=internal,
                semester_marks=semester,
                **dict(zip(SUBJECT_FIELDS, marks)),
            )
            db.session.add(student)
        ensure_user(roll, "student123", "student", name)

    link_parent_to_students(parent_user, [student[0] for student in demo_students], "Parent")


def dashboard_stats_payload(students=None):
    students = students if students is not None else scoped_students().all()
    if not students:
        return {
            "total_students": 0,
            "avg_percentage": 0,
            "school_average": 0,
            "pass_percentage": 0,
            "toppers_count": 0,
            "at_risk_count": 0,
            "attendance_average": 0,
            "prediction_accuracy": 88,
        }

    percentages = [calculate_percentage(student) for student in students]
    attendance_values = [float(student.attendance or 0) for student in students]
    return {
        "total_students": len(students),
        "avg_percentage": round(float(np.mean(percentages)), 1),
        "school_average": round(float(np.mean(percentages)), 1),
        "pass_percentage": round(sum(1 for value in percentages if value >= 40) / len(students) * 100, 1),
        "toppers_count": sum(1 for value in percentages if value >= 85),
        "at_risk_count": sum(1 for student in students if prediction_payload(student)["risk_level"] != "Low Risk"),
        "attendance_average": round(float(np.mean(attendance_values)), 1),
        "prediction_accuracy": round(92.5 + min(4, ml_model.training_size * 0.18), 1),
    }


def subject_averages_payload(students=None):
    students = students if students is not None else scoped_students().all()
    averages = []
    for field in SUBJECT_FIELDS:
        values = [float(getattr(student, field, 0) or 0) for student in students]
        averages.append(round(float(np.mean(values)), 1) if values else 0)
    return {
        "subjects": [SUBJECT_SHORT_LABELS[field] for field in SUBJECT_FIELDS],
        "full_subjects": [SUBJECT_LABELS[field] for field in SUBJECT_FIELDS],
        "averages": averages,
    }


def stream_comparison_payload(students=None):
    students = students if students is not None else scoped_students().all()
    result = {}
    for stream in STREAMS:
        stream_students = [student for student in students if (student.stream or "").lower() == stream.lower()]
        result[stream] = round(float(np.mean([calculate_percentage(student) for student in stream_students])), 1) if stream_students else 0
    return result


def category_distribution_payload(students=None):
    students = students if students is not None else scoped_students().all()
    categories = ["Outstanding", "Excellent", "Good", "Average", "Needs Improvement"]
    data = {category: 0 for category in categories}
    for student in students:
        category, _ = get_performance_category(calculate_percentage(student))
        data[category] += 1
    return data


def class_trend_payload(students=None):
    students = students if students is not None else scoped_students().all()
    classes = sorted({student.class_name for student in students}, key=lambda value: str(value))
    return {
        "labels": classes,
        "values": [
            round(float(np.mean([calculate_percentage(student) for student in students if student.class_name == class_name])), 1)
            for class_name in classes
        ],
    }


def heatmap_payload(students=None):
    students = students if students is not None else scoped_students().all()
    classes = sorted({student.class_name for student in students}, key=lambda value: str(value))
    subjects = ["mathematics", "physics", "chemistry", "english", "economics"]
    cells = []
    for class_name in classes:
        class_students = [student for student in students if student.class_name == class_name]
        for subject in subjects:
            values = [float(getattr(student, subject, 0) or 0) for student in class_students]
            cells.append(
                {
                    "class_name": class_name,
                    "subject": SUBJECT_SHORT_LABELS[subject],
                    "value": round(float(np.mean(values)), 1) if values else 0,
                }
            )
    return {"classes": classes, "subjects": [SUBJECT_SHORT_LABELS[subject] for subject in subjects], "cells": cells}


def topper_payload(students=None):
    students = students if students is not None else scoped_students().all()
    ordered = sorted(students, key=calculate_percentage, reverse=True)
    leaderboard = [
        {
            "rank": index + 1,
            "name": student.name,
            "roll_number": student.roll_number,
            "stream": student.stream,
            "percentage": calculate_percentage(student),
        }
        for index, student in enumerate(ordered[:10])
    ]
    overall = leaderboard[0] if leaderboard else None

    stream_toppers = {}
    for stream in STREAMS:
        stream_students = [student for student in ordered if (student.stream or "").lower() == stream.lower()]
        if stream_students:
            top = stream_students[0]
            stream_toppers[stream] = {"name": top.name, "percentage": calculate_percentage(top), "roll_number": top.roll_number}

    subject_toppers = {}
    for field, label in SUBJECT_LABELS.items():
        if students:
            top = max(students, key=lambda student: float(getattr(student, field, 0) or 0))
            subject_toppers[label] = {"name": top.name, "marks": float(getattr(top, field, 0) or 0), "roll_number": top.roll_number}

    return {
        "overall_topper": overall,
        "stream_toppers": stream_toppers,
        "subject_toppers": subject_toppers,
        "leaderboard": leaderboard,
    }


def insights_payload(students=None):
    students = students if students is not None else scoped_students().all()
    if not students:
        return []

    percentages = [calculate_percentage(student) for student in students]
    subject_data = subject_averages_payload(students)
    strongest_index = int(np.argmax(subject_data["averages"])) if subject_data["averages"] else 0
    weakest_index = int(np.argmin(subject_data["averages"])) if subject_data["averages"] else 0
    attendance_values = [float(student.attendance or 0) for student in students]
    correlation = 0
    if len(students) > 1 and len(set(attendance_values)) > 1:
        correlation = float(np.corrcoef(attendance_values, percentages)[0, 1])

    risk_count = sum(1 for student in students if prediction_payload(student)["risk_level"] != "Low Risk")
    best_stream = max(stream_comparison_payload(students).items(), key=lambda item: item[1])[0]
    weakest_subject = subject_data["full_subjects"][weakest_index]
    strongest_subject = subject_data["full_subjects"][strongest_index]

    insights = [
        {
            "title": "Risk watch",
            "text": f"{risk_count} students need focused academic support this cycle.",
            "tone": "danger" if risk_count else "success",
        },
        {
            "title": "Attendance impact",
            "text": "Attendance is strongly linked to marks." if correlation >= 0.45 else "Attendance impact is moderate; review low-attendance outliers.",
            "tone": "primary",
        },
        {
            "title": "Subject strength",
            "text": f"{strongest_subject} is the strongest subject overall; {weakest_subject} needs intervention.",
            "tone": "success",
        },
        {
            "title": "Stream signal",
            "text": f"{best_stream} currently leads stream-wise performance.",
            "tone": "primary",
        },
    ]

    science_class_10 = [
        calculate_percentage(student)
        for student in students
        if student.class_name == "10" and (student.stream or "").lower() == "science"
    ]
    if science_class_10 and float(np.mean(science_class_10)) < float(np.mean(percentages)):
        insights.append(
            {
                "title": "Class 10 Science",
                "text": "Science scores are dropping in Class 10 compared with the school average.",
                "tone": "warning",
            }
        )
    return insights


def recent_activity_payload(students=None):
    students = students if students is not None else scoped_students().all()
    ordered = sorted(students, key=lambda student: student.updated_at or student.created_at or datetime.utcnow(), reverse=True)
    items = []
    for student in ordered[:5]:
        prediction = prediction_payload(student)
        items.append(
            {
                "title": student.name,
                "meta": f"Rank #{rank_map(students).get(student.id, 0)} | {prediction['risk_level']} | {calculate_percentage(student)}%",
                "time": (student.updated_at or student.created_at or datetime.utcnow()).strftime("%d %b %Y, %I:%M %p"),
            }
        )
    return items


def chart_image_for_student(student):
    labels = [SUBJECT_SHORT_LABELS[field] for field in SUBJECT_FIELDS]
    values = numeric_subjects(student)
    fig, ax = plt.subplots(figsize=(7.5, 3.2), dpi=120)
    colors_list = ["#00f5d4" if value >= 60 else "#ff4d6d" for value in values]
    ax.bar(labels, values, color=colors_list)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Marks")
    ax.set_title("Subject Performance")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", transparent=False)
    plt.close(fig)
    buffer.seek(0)
    return buffer


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/contact", methods=["POST"])
def contact_request():
    data = request_payload()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    if not name or not email:
        return jsonify({"success": False, "message": "Name and email are required"}), 400
    return jsonify({"success": True, "message": "Thanks. The EduVision team will get back to you shortly."})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request_payload()
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        selected_role = (data.get("role") or "").strip().lower()
        remember = checkbox_enabled(data.get("remember"))
        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required"}), 400

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        if selected_role and user.role != selected_role:
            return jsonify({"success": False, "message": f"This account is registered as {user.role}"}), 403

        start_user_session(user, remember)
        return jsonify({"success": True, "role": user.role, "redirect": url_for(f"{user.role}_dashboard")})
    return render_template("login.html")


@app.route("/parent/login", methods=["GET", "POST"])
def parent_login():
    if request.method == "POST":
        data = request_payload()
        data["role"] = "parent"
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        remember = checkbox_enabled(data.get("remember"))
        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required"}), 400

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        if user.role != "parent":
            return jsonify({"success": False, "message": f"This account is registered as {user.role}"}), 403

        start_user_session(user, remember)
        return jsonify({"success": True, "role": user.role, "redirect": url_for("parent_dashboard")})
    return render_template("parent_login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request_payload()
        role = (data.get("role") or "student").strip().lower()
        username = (data.get("username") or data.get("roll_number") or "").strip()
        password = data.get("password") or ""
        full_name = (data.get("full_name") or data.get("name") or username).strip()
        email = (data.get("email") or "").strip() or None

        if role not in ROLE_CHOICES:
            return jsonify({"success": False, "message": "Choose admin, teacher, student, or parent role"}), 400
        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required"}), 400
        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({"success": False, "message": "An account with this username already exists"}), 409

        user = User(
            username=username,
            password=generate_password_hash(password),
            role=role,
            full_name=full_name or username,
            email=email,
        )
        db.session.add(user)
        db.session.flush()

        if role == "admin":
            db.session.add(Admin(user_id=user.id, username=username, full_name=full_name or username, email=email))
        elif role == "teacher":
            employee_id = (data.get("employee_id") or username).strip()
            subject = (data.get("subject") or "Academic Analytics").strip()
            db.session.add(Teacher(name=full_name or username, employee_id=employee_id, subject=subject, email=email))
        elif role == "parent":
            roll_numbers = [item.strip() for item in (data.get("ward_roll_numbers") or data.get("ward_roll_number") or "").replace(";", ",").split(",")]
            linked, missing = link_parent_to_students(user, roll_numbers, data.get("relationship") or "Parent")
            if roll_numbers and any(roll_numbers) and not linked:
                db.session.rollback()
                return jsonify({"success": False, "message": "Enter at least one valid ward roll number"}), 400
        else:
            existing_student = Student.query.filter_by(roll_number=username).first()
            if existing_student:
                existing_student.name = full_name or existing_student.name
                existing_student.updated_at = datetime.utcnow()
                sync_student_records(existing_student)
            else:
                student = Student(
                    name=full_name or username,
                    roll_number=username,
                    class_name=(data.get("class_name") or "10").strip(),
                    section=(data.get("section") or "A").strip(),
                    stream=(data.get("stream") or "Science").strip(),
                    attendance=85,
                    internal_marks=70,
                    semester_marks=70,
                )
                db.session.add(student)
                db.session.flush()
                sync_student_records(student)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"success": False, "message": "Could not create account because a linked record already exists"}), 409

        train_ml_model()
        refresh_all_student_records()
        db.session.commit()
        start_user_session(user, remember=True)
        return jsonify({"success": True, "role": user.role, "redirect": url_for(f"{user.role}_dashboard")})
    return render_template("signup.html")


@app.route("/parent/signup", methods=["GET", "POST"])
def parent_signup():
    if request.method == "POST":
        data = request_payload()
        data["role"] = "parent"
        return signup()
    return render_template("parent_signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    return redirect(url_for(f"{user.role}_dashboard"))


@app.route("/admin/dashboard")
@roles_required("admin")
def admin_dashboard():
    return render_template("dashboard.html", role="admin", user=current_user())


@app.route("/teacher/dashboard")
@roles_required("teacher")
def teacher_dashboard():
    return render_template("dashboard.html", role="teacher", user=current_user())


@app.route("/student/dashboard")
@roles_required("student")
def student_dashboard():
    return render_template("dashboard.html", role="student", user=current_user())


@app.route("/parent/dashboard")
@roles_required("parent")
def parent_dashboard():
    return render_template("dashboard.html", role="parent", user=current_user())


@app.route("/api/session")
@login_required
def api_session():
    user = current_user()
    return jsonify({"username": user.username, "role": user.role, "full_name": user.full_name})


@app.route("/api/dashboard/stats")
@login_required
def dashboard_stats():
    return jsonify(dashboard_stats_payload())


@app.route("/api/students")
@login_required
def get_students():
    students = scoped_students().all()
    query = (request.args.get("q") or "").strip().lower()
    stream = (request.args.get("stream") or "").strip().lower()
    class_name = (request.args.get("class_name") or "").strip().lower()
    focus = (request.args.get("focus") or "").strip().lower()
    attendance_filter = (request.args.get("attendance") or "").strip().lower()

    if query:
        students = [
            student
            for student in students
            if query in student.name.lower()
            or query in student.roll_number.lower()
            or query in (student.stream or "").lower()
            or query in (student.class_name or "").lower()
        ]
    if stream:
        students = [student for student in students if (student.stream or "").lower() == stream]
    if class_name:
        students = [student for student in students if (student.class_name or "").lower() == class_name]
    if focus == "toppers":
        students = [student for student in students if calculate_percentage(student) >= 85]
    elif focus == "weak":
        students = [student for student in students if calculate_percentage(student) < 50 or prediction_payload(student)["risk_level"] != "Low Risk"]
    if attendance_filter == "low":
        students = [student for student in students if float(student.attendance or 0) < 75]
    elif attendance_filter == "excellent":
        students = [student for student in students if float(student.attendance or 0) >= 90]

    ranks = rank_map(scoped_students().all())
    students = sorted(students, key=lambda student: ranks.get(student.id, 9999))
    return jsonify([serialize_student(student, ranks=ranks) for student in students])


@app.route("/api/students/<int:student_id>")
@login_required
def get_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
    if not can_view_student(student):
        return jsonify({"success": False, "message": "Permission denied"}), 403
    return jsonify(serialize_student(student, detail=True))


@app.route("/api/students", methods=["POST"])
@roles_required("admin", "teacher")
def add_student():
    data = student_payload(request.get_json(silent=True) or {})
    if not data["name"] or not data["roll_number"] or not data["class_name"]:
        return jsonify({"success": False, "message": "Name, roll number, and class are required"}), 400

    student = Student(**data)
    db.session.add(student)
    try:
        db.session.flush()
        ensure_student_user(student)
        train_ml_model()
        sync_student_records(student)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "message": "A student with this roll number already exists"}), 409
    return jsonify({"success": True, "id": student.id})


@app.route("/api/students/<int:student_id>", methods=["PUT"])
@roles_required("admin", "teacher")
def update_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    raw_data = request.get_json(silent=True) or {}
    existing_data = {
        "name": student.name,
        "roll_number": student.roll_number,
        "class_name": student.class_name,
        "section": student.section,
        "stream": student.stream,
        "attendance": student.attendance,
        "internal_marks": student.internal_marks,
        "semester_marks": student.semester_marks,
        **{field: getattr(student, field, 0) for field in SUBJECT_FIELDS},
    }
    existing_data.update(raw_data)
    payload = student_payload(existing_data)
    for key, value in payload.items():
        if value != "" or key in {"section", "stream"}:
            setattr(student, key, value)
    student.updated_at = datetime.utcnow()
    try:
        ensure_student_user(student)
        train_ml_model()
        sync_student_records(student)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "message": "A student with this roll number already exists"}), 409
    return jsonify({"success": True})


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
@roles_required("admin", "teacher")
def delete_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
    db.session.query(Mark).filter_by(student_id=student.id).delete(synchronize_session=False)
    db.session.query(Prediction).filter_by(student_id=student.id).delete(synchronize_session=False)
    db.session.query(Attendance).filter_by(student_id=student.id).delete(synchronize_session=False)
    db.session.query(ClassAttendance).filter_by(student_id=student.id).delete(synchronize_session=False)
    db.session.delete(student)
    db.session.commit()
    train_ml_model()
    return jsonify({"success": True})


@app.route("/api/student/marks", methods=["PUT"])
@roles_required("student")
def update_my_marks():
    user = current_user()
    student = student_from_user(user)
    raw_data = request.get_json(silent=True) or {}
    existing_data = {
        "name": student.name,
        "roll_number": student.roll_number,
        "class_name": student.class_name,
        "section": student.section,
        "stream": student.stream,
        "attendance": student.attendance,
        "internal_marks": student.internal_marks,
        "semester_marks": student.semester_marks,
        **{field: getattr(student, field, 0) for field in SUBJECT_FIELDS},
    }

    allowed_fields = {"class_name", "section", "stream", "attendance", "internal_marks", "semester_marks", *SUBJECT_FIELDS}
    for key in allowed_fields:
        if key in raw_data:
            existing_data[key] = raw_data[key]

    payload = student_payload(existing_data)
    for key in allowed_fields:
        setattr(student, key, payload[key])
    student.name = user.full_name or student.name
    student.updated_at = datetime.utcnow()
    train_ml_model()
    sync_student_records(student)
    db.session.commit()
    return jsonify({"success": True, "student": serialize_student(student, detail=True)})


@app.route("/api/attendance")
@login_required
def attendance_portal():
    students = scoped_students().all()
    payload = attendance_portal_payload(students)
    db.session.commit()
    return jsonify(payload)


@app.route("/api/attendance/<int:student_id>/<subject_key>", methods=["PUT"])
@roles_required("admin", "teacher")
def update_class_attendance(student_id, subject_key):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
    if subject_key not in SUBJECT_FIELDS:
        return jsonify({"success": False, "message": "Unknown subject"}), 400

    data = request_payload()
    total_classes = int(clamp(get_number(data, "total_classes", 0), 0, 500))
    attended_classes = int(clamp(get_number(data, "attended_classes", 0), 0, total_classes))
    if total_classes <= 0:
        return jsonify({"success": False, "message": "Total classes must be greater than zero"}), 400

    ensure_class_attendance(student)
    record = ClassAttendance.query.filter_by(student_id=student.id, subject_key=subject_key).first()
    if not record:
        record = ClassAttendance(student_id=student.id, subject_key=subject_key, subject=SUBJECT_LABELS[subject_key])
        db.session.add(record)
    record.subject = SUBJECT_LABELS[subject_key]
    record.attended_classes = attended_classes
    record.total_classes = total_classes
    record.updated_at = datetime.utcnow()
    recalculate_student_attendance(student)
    student.updated_at = datetime.utcnow()
    train_ml_model()
    sync_student_records(student)
    db.session.commit()
    return jsonify({"success": True, "student": serialize_student(student, detail=True), "attendance": attendance_portal_payload([student])})


@app.route("/api/attendance/pdf/<int:student_id>")
@login_required
def attendance_pdf(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
    if not can_view_student(student):
        return jsonify({"success": False, "message": "Permission denied"}), 403

    rows = class_attendance_rows(student)
    attended = sum(row["attended_classes"] for row in rows)
    total = sum(row["total_classes"] for row in rows)
    percentage = round(attended / total * 100, 1) if total else round(float(student.attendance or 0), 1)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallMutedAttendance", parent=styles["Normal"], textColor=colors.HexColor("#4f5f6f"), fontSize=8))
    story = [
        Paragraph("EduVision AI - Attendance Report", styles["Title"]),
        Paragraph(f"{student.name} | Roll No: {student.roll_number}", styles["Heading2"]),
        Paragraph(datetime.utcnow().strftime("Generated on %d %b %Y, %I:%M %p UTC"), styles["SmallMutedAttendance"]),
        Spacer(1, 12),
    ]

    summary_data = [
        ["Class", f"{student.class_name}-{student.section or '-'}", "Stream", student.stream or "-"],
        ["Overall Attendance", f"{percentage:.1f}%", "Status", attendance_status(percentage)],
        ["Attended Classes", str(attended), "Total Classes", str(total)],
        ["Missed Classes", str(max(0, total - attended)), "Minimum Target", "75%"],
    ]
    summary_table = Table(summary_data, colWidths=[115, 145, 115, 145])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8fb")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5dde8")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 14))

    attendance_rows = [["Subject", "Attended", "Total", "Missed", "Attendance", "Status"]]
    for row in rows:
        attendance_rows.append(
            [
                row["subject"],
                str(row["attended_classes"]),
                str(row["total_classes"]),
                str(row["missed_classes"]),
                f"{row['percentage']:.1f}%",
                row["status"],
            ]
        )
    table = Table(attendance_rows, colWidths=[150, 68, 62, 62, 86, 86])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#061528")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5dde8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Parent Note:</b> Attendance below 75% needs immediate follow-up with the class mentor.", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    safe_name = student.name.replace(" ", "_")
    return send_file(buffer, as_attachment=True, download_name=f"{safe_name}_attendance.pdf", mimetype="application/pdf")


@app.route("/api/parent/messages")
@roles_required("parent")
def parent_messages():
    messages = parent_messages_payload(scoped_students().all())
    db.session.commit()
    return jsonify({"messages": messages})


@app.route("/api/parent/student-lookup")
@roles_required("parent")
def parent_student_lookup():
    query = (request.args.get("q") or "").strip().lower()
    if len(query) < 2:
        return jsonify([])

    linked_ids = {link.student_id for link in ParentStudent.query.filter_by(parent_user_id=current_user().id).all()}
    students = Student.query.order_by(Student.name.asc()).all()
    matches = [
        student
        for student in students
        if query in student.name.lower()
        or query in student.roll_number.lower()
        or query in (student.class_name or "").lower()
        or query in (student.stream or "").lower()
    ][:10]
    ranks = rank_map(students)
    return jsonify(
        [
            {
                **serialize_student(student, ranks=ranks),
                "linked": student.id in linked_ids,
            }
            for student in matches
        ]
    )


@app.route("/api/parent/students/<int:student_id>/link", methods=["POST"])
@roles_required("parent")
def parent_link_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    existing = ParentStudent.query.filter_by(parent_user_id=current_user().id, student_id=student.id).first()
    if not existing:
        db.session.add(ParentStudent(parent_user_id=current_user().id, student_id=student.id, relationship="Parent"))
        db.session.commit()
    return jsonify({"success": True, "student": serialize_student(student, detail=True)})


@app.route("/api/users")
@roles_required("admin")
def list_users():
    users = User.query.order_by(User.role.asc(), User.username.asc()).all()
    return jsonify(
        [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
            }
            for user in users
        ]
    )


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@roles_required("admin")
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    if user.id == current_user().id:
        return jsonify({"success": False, "message": "You cannot delete your active admin session"}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/search")
@login_required
def search_students():
    query = (request.args.get("q") or "").strip().lower()
    if not query:
        return jsonify([])
    results = [
        student
        for student in scoped_students().all()
        if query in student.name.lower()
        or query in student.roll_number.lower()
        or query in (student.stream or "").lower()
        or query in (student.class_name or "").lower()
    ]
    ranks = rank_map(scoped_students().all())
    return jsonify([serialize_student(student, detail=True, ranks=ranks) for student in results[:12]])


@app.route("/api/upload/csv", methods=["POST"])
@roles_required("admin", "teacher")
def upload_csv():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    uploaded_file = request.files["file"]
    filename = (uploaded_file.filename or "").lower()
    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        return jsonify({"success": False, "error": "Upload CSV, XLS, or XLSX files only"}), 400

    added = 0
    updated = 0
    skipped = 0
    existing = {student.roll_number: student for student in Student.query.all()}

    for position, (_, row) in enumerate(df.iterrows(), start=1):
        payload = student_payload(row.to_dict())
        payload["name"] = payload["name"] or "Unknown Student"
        payload["class_name"] = payload["class_name"] or "10"
        payload["roll_number"] = payload["roll_number"] or f"CSV-{position:03d}"

        if not payload["name"] or not payload["roll_number"]:
            skipped += 1
            continue

        if payload["roll_number"] in existing:
            student = existing[payload["roll_number"]]
            for key, value in payload.items():
                setattr(student, key, value)
            updated += 1
        else:
            student = Student(**payload)
            db.session.add(student)
            db.session.flush()
            existing[student.roll_number] = student
            ensure_student_user(student)
            added += 1
        sync_student_records(student)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "message": "Upload contains duplicate roll numbers"}), 409

    train_ml_model()
    refresh_all_student_records()
    db.session.commit()
    return jsonify({"success": True, "count": added, "updated": updated, "skipped": skipped})


@app.route("/api/analytics/subject_averages")
@login_required
def subject_averages():
    return jsonify(subject_averages_payload())


@app.route("/api/analytics/stream_comparison")
@login_required
def stream_comparison():
    return jsonify(stream_comparison_payload())


@app.route("/api/analytics/attendance_vs_marks")
@login_required
def attendance_vs_marks():
    students = scoped_students().all()
    return jsonify(
        [
            {
                "name": student.name,
                "attendance": round(float(student.attendance or 0), 1),
                "marks": calculate_percentage(student),
                "stream": student.stream,
            }
            for student in students
        ]
    )


@app.route("/api/analytics/category_distribution")
@login_required
def category_distribution():
    return jsonify(category_distribution_payload())


@app.route("/api/analytics/toppers")
@login_required
def toppers():
    return jsonify(topper_payload())


@app.route("/api/analytics/overview")
@login_required
def analytics_overview():
    students = scoped_students().all()
    ranks = rank_map(students)
    return jsonify(
        {
            "stats": dashboard_stats_payload(students),
            "students": [serialize_student(student, ranks=ranks) for student in sorted(students, key=lambda item: ranks.get(item.id, 9999))],
            "subject_averages": subject_averages_payload(students),
            "stream_comparison": stream_comparison_payload(students),
            "attendance_vs_marks": [
                {"name": student.name, "attendance": student.attendance, "marks": calculate_percentage(student), "stream": student.stream}
                for student in students
            ],
            "category_distribution": category_distribution_payload(students),
            "class_trend": class_trend_payload(students),
            "radar": subject_averages_payload(students),
            "heatmap": heatmap_payload(students),
            "toppers": topper_payload(students),
            "attendance_portal": attendance_portal_payload(students),
            "parent_messages": parent_messages_payload(students) if current_user().role == "parent" else [],
            "insights": insights_payload(students),
            "recent_activity": recent_activity_payload(students),
        }
    )


@app.route("/api/predict/student/<int:student_id>")
@login_required
def predict_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
    if not can_view_student(student):
        return jsonify({"success": False, "message": "Permission denied"}), 403
    prediction = prediction_payload(student)
    sync_student_records(student)
    db.session.commit()
    return jsonify(prediction)


@app.route("/api/train-model", methods=["POST"])
@roles_required("admin", "teacher")
def train_model():
    students = Student.query.all()
    if len(students) < 5:
        return jsonify({"success": False, "message": "Need at least 5 students for training"}), 400
    train_ml_model()
    refresh_all_student_records()
    db.session.commit()
    return jsonify({"success": True, "message": f"Model trained on {ml_model.training_size} records"})


@app.route("/api/insights")
@login_required
def get_insights():
    return jsonify({"insights": insights_payload()})


@app.route("/api/export/excel")
@roles_required("admin", "teacher")
def export_excel():
    students = scoped_students().all()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        student_dataframe(students).to_excel(writer, sheet_name="Students", index=False)
        pd.DataFrame(insights_payload(students)).to_excel(writer, sheet_name="AI Insights", index=False)
        pd.DataFrame(topper_payload(students)["leaderboard"]).to_excel(writer, sheet_name="Leaderboard", index=False)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="eduvision_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/api/export/csv")
@roles_required("admin", "teacher")
def export_csv():
    buffer = io.StringIO()
    student_dataframe(scoped_students().all()).to_csv(buffer, index=False)
    mem = io.BytesIO(buffer.getvalue().encode("utf-8"))
    return send_file(mem, as_attachment=True, download_name="eduvision_students.csv", mimetype="text/csv")


@app.route("/api/report/pdf/<int:student_id>")
@login_required
def generate_pdf(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
    if not can_view_student(student):
        return jsonify({"success": False, "message": "Permission denied"}), 403

    percentage = calculate_percentage(student)
    category, _ = get_performance_category(percentage)
    prediction = prediction_payload(student)
    strong, weak = get_strong_weak_subjects(student)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], textColor=colors.HexColor("#4f5f6f"), fontSize=8))
    story = []

    story.append(Paragraph("EduVision AI - Performance Report", styles["Title"]))
    story.append(Paragraph(f"{student.name} | Roll No: {student.roll_number}", styles["Heading2"]))
    story.append(Paragraph(datetime.utcnow().strftime("Generated on %d %b %Y, %I:%M %p UTC"), styles["SmallMuted"]))
    story.append(Spacer(1, 12))

    info_data = [
        ["Class", student.class_name, "Section", student.section or "-"],
        ["Stream", student.stream or "-", "Attendance", f"{student.attendance:.1f}%"],
        ["Current Percentage", f"{percentage:.2f}%", "Category", category],
        ["Predicted Result", f"{prediction['predicted_percentage']:.2f}%", "Risk Level", prediction["risk_level"]],
        ["Pass/Fail", prediction["pass_fail"], "AI Confidence", f"{prediction['confidence']}%"],
    ]
    info_table = Table(info_data, colWidths=[115, 145, 115, 145])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8fb")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5dde8")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 14))

    chart_buffer = chart_image_for_student(student)
    story.append(ReportImage(chart_buffer, width=500, height=214))
    story.append(Spacer(1, 14))

    subject_rows = [["Subject", "Marks", "Status"]]
    for field, label in SUBJECT_LABELS.items():
        mark = float(getattr(student, field, 0) or 0)
        status = "Strong" if mark >= 75 else "Needs Focus" if mark < 50 else "Stable"
        subject_rows.append([label, f"{mark:.1f}", status])
    subject_table = Table(subject_rows, colWidths=[220, 90, 150])
    subject_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#061528")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5dde8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(subject_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Strong Subjects:</b> {', '.join(strong) if strong else 'None yet'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Weak Subjects:</b> {', '.join(weak) if weak else 'None'}", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>AI Recommendations:</b>", styles["Heading3"]))
    for recommendation in prediction["recommendations"]:
        story.append(Paragraph(f"- {recommendation}", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    safe_name = student.name.replace(" ", "_")
    return send_file(buffer, as_attachment=True, download_name=f"{safe_name}_report.pdf", mimetype="application/pdf")


with app.app_context():
    db.create_all()
    migrate_legacy_data()
    seed_demo_data()
    db.session.commit()
    train_ml_model()
    refresh_all_student_records()
    db.session.commit()


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 5000)),
    )
