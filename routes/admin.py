from flask import Blueprint, request, jsonify
from models.database import db, Student, SubjectResult
from utils.excel_parser import parse_excel

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin_bp.route('/upload', methods=['POST'])
def upload_results():
    """
    Upload an Excel file of student results.

    Form fields:
      - file: Excel file (.xlsx / .xls)
      - exam_name: (optional) name of the exam, e.g. "Mid-Term 2024"
      - overwrite: (optional) 'true' to overwrite existing records
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request. Use key "file".'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .xlsx and .xls allowed.'}), 400

    exam_name = request.form.get('exam_name', 'General').strip() or 'General'
    overwrite = request.form.get('overwrite', 'false').lower() == 'true'

    file_bytes = file.read()
    if len(file_bytes) == 0:
        return jsonify({'error': 'Uploaded file is empty.'}), 400

    parsed = parse_excel(file_bytes, exam_name=exam_name)

    if parsed['errors'] and not parsed['students']:
        return jsonify({'error': 'File parsing failed.', 'details': parsed['errors']}), 422

    inserted = 0
    skipped = 0
    updated = 0

    for s in parsed['students']:
        sid = s['student_id'].strip().upper()
        existing = Student.query.get(sid)

        if existing:
            if not overwrite:
                skipped += 1
                continue
            # Delete old subject results before updating
            SubjectResult.query.filter_by(student_id=sid).delete()
            existing.name = s['name']
            existing.class_name = s['class_name']
            existing.exam_name = s['exam_name']
            for sub in s['subjects']:
                db.session.add(SubjectResult(
                    student_id=sid,
                    subject_name=sub['subject_name'],
                    marks_obtained=sub['marks_obtained'],
                    max_marks=sub['max_marks']
                ))
            updated += 1
        else:
            student = Student(
                id=sid,
                name=s['name'],
                class_name=s['class_name'],
                exam_name=s['exam_name']
            )
            db.session.add(student)
            db.session.flush()  # get the ID before adding children
            for sub in s['subjects']:
                db.session.add(SubjectResult(
                    student_id=sid,
                    subject_name=sub['subject_name'],
                    marks_obtained=sub['marks_obtained'],
                    max_marks=sub['max_marks']
                ))
            inserted += 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    return jsonify({
        'message': 'Upload complete.',
        'inserted': inserted,
        'updated': updated,
        'skipped': skipped,
        'parse_warnings': parsed['warnings'],
        'parse_errors': parsed['errors']
    }), 200


@admin_bp.route('/students', methods=['GET'])
def list_students():
    """List all students (paginated)."""
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    class_name = request.args.get('class_name', '').strip()
    exam_name = request.args.get('exam_name', '').strip()

    query = Student.query
    if class_name:
        query = query.filter(Student.class_name.ilike(f'%{class_name}%'))
    if exam_name:
        query = query.filter(Student.exam_name.ilike(f'%{exam_name}%'))

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'students': [s.to_dict() for s in paginated.items],
        'total': paginated.total,
        'page': page,
        'pages': paginated.pages
    }), 200


@admin_bp.route('/student/<string:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student and their results."""
    student = Student.query.get(student_id.strip().upper())
    if not student:
        return jsonify({'error': 'Student not found.'}), 404
    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': f'Student {student_id} deleted.'}), 200


@admin_bp.route('/exams', methods=['GET'])
def list_exams():
    """Return distinct exam names in DB."""
    exams = db.session.query(Student.exam_name).distinct().all()
    return jsonify({'exams': [e[0] for e in exams]}), 200
