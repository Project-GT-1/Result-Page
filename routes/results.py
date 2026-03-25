from flask import Blueprint, jsonify, send_file, request
from models.database import Student
from utils.pdf_generator import generate_marksheet
import io

results_bp = Blueprint('results', __name__)


@results_bp.route('/result/<string:student_id>', methods=['GET'])
def get_result(student_id):
    """Fetch a student's result by ID."""
    student = Student.query.get(student_id.strip().upper())
    if not student:
        return jsonify({'error': f'No result found for student ID "{student_id}"'}), 404
    return jsonify(student.to_dict()), 200


@results_bp.route('/result/<string:student_id>/pdf', methods=['GET'])
def download_pdf(student_id):
    """Download marksheet PDF for a student."""
    student = Student.query.get(student_id.strip().upper())
    if not student:
        return jsonify({'error': f'No result found for student ID "{student_id}"'}), 404

    try:
        pdf_bytes = generate_marksheet(student.to_dict())
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"marksheet_{student_id}.pdf"
    )


@results_bp.route('/results/search', methods=['GET'])
def search_results():
    """
    Search results with optional filters.
    Query params: class_name, exam_name, page, per_page
    """
    class_name = request.args.get('class_name', '').strip()
    exam_name = request.args.get('exam_name', '').strip()
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)

    query = Student.query
    if class_name:
        query = query.filter(Student.class_name.ilike(f'%{class_name}%'))
    if exam_name:
        query = query.filter(Student.exam_name.ilike(f'%{exam_name}%'))

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'results': [s.to_dict() for s in paginated.items],
        'total': paginated.total,
        'page': page,
        'pages': paginated.pages
    }), 200
