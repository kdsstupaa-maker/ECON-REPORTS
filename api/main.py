from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
import sqlite3
import os
import json

app = FastAPI(title="Reports API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bok_news.db")

class Report(BaseModel):
    id: int
    report_key: str
    source_name: str
    title: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    summary_data: Optional[Any] = None

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/reports", response_model=List[Report])
def get_reports(
    search: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM reports WHERE 1=1"
    params = []
    
    if search:
        query += " AND (title LIKE ? OR summary_json LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    if source:
        query += " AND source_name = ?"
        params.append(source)
        
    query += " ORDER BY publish_date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    reports = []
    for row in rows:
        row_dict = dict(row)
        # Parse summary JSON if present
        summary = row_dict.get('summary_json')
        if summary:
            try:
                row_dict['summary_data'] = json.loads(summary)
            except:
                row_dict['summary_data'] = None
        
        reports.append(Report(**row_dict))
        
    conn.close()
    return reports

@app.get("/api/reports/{report_id}/pdf")
def get_report_pdf(report_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pdf_path, title FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row['pdf_path']:
        raise HTTPException(status_code=404, detail="PDF not found")
        
    pdf_path = row['pdf_path']
    if pdf_path.startswith("http://") or pdf_path.startswith("https://"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=pdf_path)
        
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
        
    filename = f"{row['title']}.pdf".replace("/", "_").replace("\\", "_")
    return FileResponse(pdf_path, filename=filename, media_type='application/pdf')
