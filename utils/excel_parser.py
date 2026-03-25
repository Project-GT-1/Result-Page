import pandas as pd
import io


REQUIRED_COLUMNS = {'student_id', 'name', 'class'}


def parse_excel(file_bytes: bytes, exam_name: str = 'General') -> dict:
    """
    Parse uploaded Excel file and return structured data.

    Expected Excel columns:
      student_id | name | class | Subject1 | Subject2 | ... | SubjectN
      (max_marks row optional: put 'MAX' in student_id column)

    Returns:
        {
            'students': [...],
            'errors': [...],
            'warnings': [...]
        }
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
    except Exception as e:
        return {'students': [], 'errors': [f'Could not read file: {str(e)}'], 'warnings': []}

    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return {
            'students': [],
            'errors': [f'Missing required columns: {", ".join(missing)}'],
            'warnings': []
        }

    # Detect subject columns (everything that's not id/name/class)
    meta_cols = {'student_id', 'name', 'class'}
    subject_cols = [c for c in df.columns if c not in meta_cols]

    if not subject_cols:
        return {'students': [], 'errors': ['No subject columns found.'], 'warnings': []}

    # Extract max_marks row if present
    max_marks_map = {s: 100.0 for s in subject_cols}
    max_row_mask = df['student_id'].str.upper().str.strip() == 'MAX'
    if max_row_mask.any():
        max_row = df[max_row_mask].iloc[0]
        for s in subject_cols:
            try:
                max_marks_map[s] = float(max_row[s])
            except (ValueError, TypeError):
                pass
        df = df[~max_row_mask].copy()

    students = []
    errors = []
    warnings = []
    seen_ids = set()

    for idx, row in df.iterrows():
        row_num = idx + 2  # human-readable row number
        sid = str(row.get('student_id', '')).strip()
        name = str(row.get('name', '')).strip()
        cls = str(row.get('class', '')).strip()

        if not sid or sid.lower() == 'nan':
            warnings.append(f'Row {row_num}: missing student_id — skipped')
            continue
        if not name or name.lower() == 'nan':
            warnings.append(f'Row {row_num} ({sid}): missing name — skipped')
            continue
        if sid in seen_ids:
            warnings.append(f'Row {row_num}: duplicate student_id "{sid}" — skipped')
            continue
        seen_ids.add(sid)

        subjects = []
        has_error = False
        for s in subject_cols:
            raw = str(row.get(s, '')).strip()
            if raw == '' or raw.lower() == 'nan':
                warnings.append(f'Row {row_num} ({sid}): missing marks for "{s}" — set to 0')
                marks = 0.0
            else:
                try:
                    marks = float(raw)
                except ValueError:
                    errors.append(f'Row {row_num} ({sid}): invalid marks "{raw}" for "{s}" — skipped student')
                    has_error = True
                    break
                if marks < 0 or marks > max_marks_map[s]:
                    warnings.append(f'Row {row_num} ({sid}): marks {marks} out of range for "{s}"')
            subjects.append({
                'subject_name': s.title(),
                'marks_obtained': marks,
                'max_marks': max_marks_map[s]
            })

        if has_error:
            continue

        students.append({
            'student_id': sid,
            'name': name,
            'class_name': cls,
            'exam_name': exam_name,
            'subjects': subjects
        })

    return {'students': students, 'errors': errors, 'warnings': warnings}
