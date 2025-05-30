from flask_sqlalchemy import SQLAlchemy
from datetime import date
from flask import Flask

# إعداد التطبيق وقاعدة البيانات
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- بداية النماذج ---
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    absences = db.relationship('Absence', backref='student', lazy=True)

    def __repr__(self):
        return f'<Student {self.name}>'

class Absence(db.Model):
    __tablename__ = 'absences'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    absence_type = db.Column(db.String(10), nullable=False, default='full') # 'full' أو 'half'
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)

    def __repr__(self):
        return f'<Absence {self.student_id} on {self.date} ({self.absence_type})>'

class Holiday(db.Model):
    __tablename__ = 'holidays'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Holiday {self.name} on {self.date}>'
