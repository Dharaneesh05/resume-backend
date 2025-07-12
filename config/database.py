import sqlite3
from datetime import datetime
from flask import g
def get_database_connection():
    """Get or create a database connection for the current request."""
    if 'db' not in g:
        g.db = sqlite3.connect('resumes.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_database_connection(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_database(app=None):
    conn = sqlite3.connect('resumes.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resume_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            linkedin TEXT,
            github TEXT,
            portfolio TEXT,
            summary TEXT,
            target_role TEXT,
            target_category TEXT,
            education TEXT,
            experience TEXT,
            projects TEXT,
            skills TEXT,
            template TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resume_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER,
            ats_score REAL,
            keyword_match_score REAL,
            format_score REAL,
            section_score REAL,
            missing_skills TEXT,
            recommendations TEXT,
            FOREIGN KEY (resume_id) REFERENCES resume_data(id)
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            rating INTEGER,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


    if app:
        app.teardown_appcontext(close_database_connection)

def save_resume_data(resume_data):
    """Save resume metadata and return the resume ID."""
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO resume_data (
            name, email, phone, linkedin, github, portfolio,
            summary, target_role, target_category, education,
            experience, projects, skills, template
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        resume_data['personal_info'].get('name', ''),
        resume_data['personal_info'].get('email', ''),
        resume_data['personal_info'].get('phone', ''),
        resume_data['personal_info'].get('linkedin', ''),
        resume_data['personal_info'].get('github', ''),
        resume_data['personal_info'].get('portfolio', ''),
        resume_data.get('summary', ''),
        resume_data.get('target_role', ''),
        resume_data.get('target_category', ''),
        str(resume_data.get('education', [])),
        str(resume_data.get('experience', [])),
        str(resume_data.get('projects', [])),
        str(resume_data.get('skills', [])),
        resume_data.get('template', '')
    ))

    resume_id = cursor.lastrowid
    conn.commit()
    return resume_id

def save_analysis_data(resume_id, analysis_data):
    """Save analysis results for a resume."""
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO resume_analysis (
            resume_id, ats_score, keyword_match_score, format_score,
            section_score, missing_skills, recommendations
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        resume_id,
        analysis_data.get('ats_score', 0.0),
        analysis_data.get('keyword_match_score', 0.0),
        analysis_data.get('format_score', 0.0),
        analysis_data.get('section_score', 0.0),
        analysis_data.get('missing_skills', ''),
        analysis_data.get('recommendations', '')
    ))

    conn.commit()

def get_all_analysis():
    """Retrieve all analysis results."""
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT rd.target_category, rd.target_role, rd.created_at, rd.skills, ra.*
        FROM resume_analysis ra
        JOIN resume_data rd ON ra.resume_id = rd.id
    ''')
    rows = cursor.fetchall()
    return rows

def save_feedback(feedback_data):
    """Save user feedback to the database."""
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO feedback (name, email, rating, comments)
        VALUES (?, ?, ?, ?)
    ''', (
        feedback_data.get('name', ''),
        feedback_data.get('email', ''),
        feedback_data.get('rating', 0),
        feedback_data.get('comments', '')
    ))

    conn.commit()

def get_feedback_stats():
    """Retrieve feedback statistics."""
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT rating, COUNT(*) as count FROM feedback GROUP BY rating')
    ratings = cursor.fetchall()
    rating_distribution = {str(i): 0 for i in range(1, 6)}
    total_feedback = 0
    total_rating = 0

    for rating, count in ratings:
        rating_distribution[str(rating)] = count
        total_feedback += count
        total_rating += rating * count

    avg_rating = total_rating / total_feedback if total_feedback > 0 else 0
    return {
        'average_rating': round(avg_rating, 2),
        'total_feedback': total_feedback,
        'rating_distribution': rating_distribution
    }