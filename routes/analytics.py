from flask import Blueprint, jsonify, request
from models.database import db, Student, SubjectResult
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/summary', methods=['GET'])
def summary():
    """Overall summary stats. Filter by exam_name or class_name via query params."""
    exam_name = request.args.get('exam_name', '').strip()
    class_name = request.args.get('class_name', '').strip()

    query = Student.query
    if exam_name:
        query = query.filter(Student.exam_name.ilike(f'%{exam_name}%'))
    if class_name:
        query = query.filter(Student.class_name.ilike(f'%{class_name}%'))

    students = query.all()
    if not students:
        return jsonify({'error': 'No data found for given filters.'}), 404

    total = len(students)
    passed = sum(1 for s in students if s.status == 'Pass')
    failed = total - passed
    percentages = [s.percentage for s in students]

    grade_dist = {}
    for s in students:
        grade_dist[s.grade] = grade_dist.get(s.grade, 0) + 1

    return jsonify({
        'total_students': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': round((passed / total) * 100, 2),
        'class_average': round(sum(percentages) / total, 2),
        'highest_percentage': round(max(percentages), 2),
        'lowest_percentage': round(min(percentages), 2),
        'grade_distribution': grade_dist
    }), 200


@analytics_bp.route('/toppers', methods=['GET'])
def toppers():
    """Top N students by percentage. Default top 10."""
    n = min(int(request.args.get('n', 10)), 50)
    exam_name = request.args.get('exam_name', '').strip()
    class_name = request.args.get('class_name', '').strip()

    query = Student.query
    if exam_name:
        query = query.filter(Student.exam_name.ilike(f'%{exam_name}%'))
    if class_name:
        query = query.filter(Student.class_name.ilike(f'%{class_name}%'))

    students = query.all()
    sorted_students = sorted(students, key=lambda s: s.percentage, reverse=True)[:n]

    return jsonify({
        'toppers': [
            {
                'rank': i + 1,
                'student_id': s.id,
                'name': s.name,
                'class_name': s.class_name,
                'percentage': s.percentage,
                'grade': s.grade
            }
            for i, s in enumerate(sorted_students)
        ]
    }), 200


@analytics_bp.route('/subject-averages', methods=['GET'])
def subject_averages():
    """Average marks per subject. Filter by exam_name or class_name."""
    exam_name = request.args.get('exam_name', '').strip()
    class_name = request.args.get('class_name', '').strip()

    query = (
        db.session.query(
            SubjectResult.subject_name,
            func.avg(SubjectResult.marks_obtained).label('avg_marks'),
            func.avg(SubjectResult.max_marks).label('avg_max'),
            func.count(SubjectResult.id).label('count')
        )
        .join(Student, Student.id == SubjectResult.student_id)
    )
    if exam_name:
        query = query.filter(Student.exam_name.ilike(f'%{exam_name}%'))
    if class_name:
        query = query.filter(Student.class_name.ilike(f'%{class_name}%'))

    rows = query.group_by(SubjectResult.subject_name).all()

    return jsonify({
        'subject_averages': [
            {
                'subject': r.subject_name,
                'avg_marks': round(r.avg_marks, 2),
                'avg_max_marks': round(r.avg_max, 2),
                'avg_percentage': round((r.avg_marks / r.avg_max) * 100, 2) if r.avg_max else 0,
                'student_count': r.count
            }
            for r in rows
        ]
    }), 200


@analytics_bp.route('/class-comparison', methods=['GET'])
def class_comparison():
    """Compare average percentage across all classes."""
    exam_name = request.args.get('exam_name', '').strip()
    query = Student.query
    if exam_name:
        query = query.filter(Student.exam_name.ilike(f'%{exam_name}%'))
    students = query.all()

    classes = {}
    for s in students:
        cls = s.class_name
        if cls not in classes:
            classes[cls] = []
        classes[cls].append(s.percentage)

    return jsonify({
        'class_comparison': [
            {
                'class_name': cls,
                'total_students': len(pcts),
                'avg_percentage': round(sum(pcts) / len(pcts), 2),
                'pass_count': sum(1 for s in students if s.class_name == cls and s.status == 'Pass'),
            }
            for cls, pcts in sorted(classes.items())
        ]
    }), 200
