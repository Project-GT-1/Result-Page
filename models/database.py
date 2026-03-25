from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    exam_name = db.Column(db.String(100), nullable=False, default='General')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship('SubjectResult', backref='student', cascade='all, delete-orphan', lazy=True)

    @property
    def total_marks(self):
        return sum(r.marks_obtained for r in self.results)

    @property
    def max_marks(self):
        return sum(r.max_marks for r in self.results)

    @property
    def percentage(self):
        if self.max_marks == 0:
            return 0.0
        return round((self.total_marks / self.max_marks) * 100, 2)

    @property
    def grade(self):
        p = self.percentage
        if p >= 90: return 'A+'
        if p >= 75: return 'A'
        if p >= 60: return 'B'
        if p >= 50: return 'C'
        if p >= 35: return 'D'
        return 'F'

    @property
    def status(self):
        # Fail if any subject below 35% or overall below 35
        failed_subjects = [r for r in self.results if r.marks_obtained < (r.max_marks * 0.35)]
        if failed_subjects or self.percentage < 35:
            return 'Fail'
        return 'Pass'

    def to_dict(self):
        return {
            'student_id': self.id,
            'name': self.name,
            'class_name': self.class_name,
            'exam_name': self.exam_name,
            'subjects': [r.to_dict() for r in self.results],
            'total_marks': self.total_marks,
            'max_marks': self.max_marks,
            'percentage': self.percentage,
            'grade': self.grade,
            'status': self.status,
            'uploaded_at': self.uploaded_at.isoformat()
        }


class SubjectResult(db.Model):
    __tablename__ = 'subject_results'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.id'), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=100)

    @property
    def subject_percentage(self):
        if self.max_marks == 0:
            return 0.0
        return round((self.marks_obtained / self.max_marks) * 100, 2)

    @property
    def subject_grade(self):
        p = self.subject_percentage
        if p >= 90: return 'A+'
        if p >= 75: return 'A'
        if p >= 60: return 'B'
        if p >= 50: return 'C'
        if p >= 35: return 'D'
        return 'F'

    def to_dict(self):
        return {
            'subject': self.subject_name,
            'marks_obtained': self.marks_obtained,
            'max_marks': self.max_marks,
            'percentage': self.subject_percentage,
            'grade': self.subject_grade
        }
