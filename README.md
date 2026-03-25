# Student Result Portal — Flask Backend

A production-ready REST API for managing student results. Supports Excel uploads, result search, PDF marksheet generation, and analytics.

---

## Project Structure

```
result_portal/
├── app.py                  # Flask app factory
├── wsgi.py                 # Gunicorn entry point
├── requirements.txt
├── render.yaml             # Render.com deploy config
├── sample_results.csv      # Sample Excel format reference
├── models/
│   └── database.py         # SQLAlchemy models (Student, SubjectResult)
├── routes/
│   ├── results.py          # Student result search + PDF download
│   ├── admin.py            # Excel upload + student management
│   └── analytics.py        # Dashboard analytics
└── utils/
    ├── excel_parser.py     # Pandas-based Excel parser + validator
    └── pdf_generator.py    # ReportLab PDF marksheet generator
```

---

## Quick Start (Local)

```bash
cd result_portal
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
FLASK_DEBUG=true python app.py
```

Server runs at `http://localhost:5000`

---

## Excel File Format

| student_id | name         | class | Mathematics | Science | English |
|------------|--------------|-------|-------------|---------|---------|
| MAX        |              |       | 100         | 100     | 100     |
| S001       | Ravi Kumar   | 10A   | 88          | 92      | 76      |
| S002       | Priya Sharma | 10A   | 95          | 98      | 89      |

- **Row with `MAX` in `student_id`**: sets max marks per subject (optional; defaults to 100)
- Subject columns: any column that is not `student_id`, `name`, or `class`
- File formats supported: `.xlsx`, `.xls`

---

## API Reference

### Student Endpoints

#### Get result by student ID
```
GET /api/result/{student_id}
```
Response:
```json
{
  "student_id": "S001",
  "name": "Ravi Kumar",
  "class_name": "10A",
  "exam_name": "Mid-Term 2024",
  "subjects": [
    {"subject": "Mathematics", "marks_obtained": 88, "max_marks": 100, "percentage": 88.0, "grade": "A"}
  ],
  "total_marks": 88,
  "max_marks": 100,
  "percentage": 88.0,
  "grade": "A",
  "status": "Pass"
}
```

#### Download PDF marksheet
```
GET /api/result/{student_id}/pdf
```
Returns a downloadable PDF file.

#### Search results
```
GET /api/results/search?class_name=10A&exam_name=Mid-Term&page=1&per_page=20
```

---

### Admin Endpoints

#### Upload Excel results
```
POST /api/admin/upload
Content-Type: multipart/form-data

file=<excel_file>
exam_name=Mid-Term 2024        (optional)
overwrite=true                 (optional, default false)
```
Response:
```json
{
  "message": "Upload complete.",
  "inserted": 45,
  "updated": 0,
  "skipped": 2,
  "parse_warnings": [],
  "parse_errors": []
}
```

#### List all students
```
GET /api/admin/students?class_name=10A&page=1&per_page=50
```

#### Delete a student
```
DELETE /api/admin/student/{student_id}
```

#### List exam names
```
GET /api/admin/exams
```

---

### Analytics Endpoints

#### Summary stats
```
GET /api/analytics/summary?exam_name=Mid-Term&class_name=10A
```
```json
{
  "total_students": 50,
  "passed": 44,
  "failed": 6,
  "pass_rate": 88.0,
  "class_average": 73.5,
  "highest_percentage": 98.0,
  "lowest_percentage": 28.0,
  "grade_distribution": {"A+": 8, "A": 14, "B": 12, "C": 10, "D": 4, "F": 2}
}
```

#### Toppers list
```
GET /api/analytics/toppers?n=10&exam_name=Mid-Term
```

#### Subject-wise averages
```
GET /api/analytics/subject-averages?exam_name=Mid-Term
```

#### Class comparison
```
GET /api/analytics/class-comparison?exam_name=Mid-Term
```

---

## Deploy to Render (Free Tier)

1. Push this folder to a GitHub repository
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render reads `render.yaml` automatically — it will:
   - Create a PostgreSQL database
   - Deploy the Flask app with Gunicorn
   - Set all environment variables
5. Done! Your API will be live at `https://student-result-portal.onrender.com`

---

## Environment Variables

| Variable       | Description                          | Default              |
|----------------|--------------------------------------|----------------------|
| `DATABASE_URL` | PostgreSQL connection string         | SQLite (local)       |
| `SECRET_KEY`   | Flask secret key                     | dev-secret (change!) |
| `FLASK_DEBUG`  | Enable debug mode (`true`/`false`)   | `false`              |

---

## Grade Scale

| Percentage | Grade |
|------------|-------|
| 90 – 100   | A+    |
| 75 – 89    | A     |
| 60 – 74    | B     |
| 50 – 59    | C     |
| 35 – 49    | D     |
| Below 35   | F     |

A student **Fails** if any single subject is below 35% OR overall percentage is below 35%.
