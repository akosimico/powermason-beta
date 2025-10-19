import pdfplumber
from datetime import datetime
import re

def parse_date(date_str):
    for fmt in ("%d-%b-%y", "%d-%b-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def extract_project_info(pdf_path):
    project_info = {
        "proj_id": None,
        "project": None,
        "location": None,
        "scope": None,
        "tasks": []
    }

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()

            # Group words by vertical position
            lines = {}
            for w in words:
                top = round(w['top'])
                lines.setdefault(top, []).append(w)

            for line_words in lines.values():
                line_words = sorted(line_words, key=lambda x: x['x0'])
                new_line = []
                buffer = ""
                prev_x = None
                for w in line_words:
                    if prev_x is not None and w['text'].replace('.', '').isdigit() and buffer.replace('.', '').isdigit() and w['x0'] - prev_x < 3:
                        buffer += w['text']
                    else:
                        if buffer:
                            new_line.append(buffer)
                        buffer = w['text']
                    prev_x = w['x1']
                if buffer:
                    new_line.append(buffer)
                line = " ".join(new_line)

                # --- Extract project headers ---
                if project_info["proj_id"] is None:
                    match = re.search(r"PROJ ID\s*[:\-]?\s*([A-Za-z0-9\-]+)", line)
                    if match:
                        project_info["proj_id"] = match.group(1).strip()
                        continue
                if project_info["project"] is None:
                    match = re.search(r"PROJECT\s*[:\-]?\s*(.+)", line)
                    if match:
                        project_info["project"] = match.group(1).strip()
                        continue
                if project_info["location"] is None:
                    match = re.search(r"LOCATION\s*[:\-]?\s*(.+)", line)
                    if match:
                        project_info["location"] = match.group(1).strip()
                        continue
                if project_info["scope"] is None:
                    match = re.search(r"SCOPE\s*[:\-]?\s*(.+)", line)
                    if match:
                        project_info["scope"] = match.group(1).strip()
                        continue

                # --- Extract tasks ---
                task_match = re.match(
                    r"(?P<task>.+?)\s+"
                    r"(?P<start>\d{1,2}-[A-Za-z]{3}-\d{2,4})\s+"
                    r"(?P<end>\d{1,2}-[A-Za-z]{3}-\d{2,4})\s+"
                    r"(?P<duration>[\d\.]+)\s+"
                    r"(?P<MH>[\d\.]+)",
                    line
                )
                if task_match:
                    project_info["tasks"].append({
        "task_name": task_match.group("task").strip(),
        "start_date": parse_date(task_match.group("start")).isoformat() if parse_date(task_match.group("start")) else None,
        "end_date": parse_date(task_match.group("end")).isoformat() if parse_date(task_match.group("end")) else None,
        "duration_days": float(task_match.group("duration")),
        "manhours": float(task_match.group("MH")),
        "scope": project_info.get("scope")  # default from header if available
    })




    return project_info
