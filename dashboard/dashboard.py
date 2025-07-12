import pandas as pd
from datetime import datetime, timedelta
from .components import DashboardComponents
import json
import io
from config.database import get_database_connection

class DashboardManager:
    def __init__(self):
        self.colors = {
            'primary': '#4CAF50',
            'secondary': '#2196F3',
            'warning': '#FFA726',
            'danger': '#F44336',
            'info': '#00BCD4',
            'success': '#66BB6A',
            'purple': '#9C27B0',
            'background': '#1E1E1E',
            'card': '#2D2D2D',
            'text': '#FFFFFF',
            'subtext': '#B0B0B0'
        }
        self.components = DashboardComponents(self.colors)

    def get_resume_metrics(self):
        """Get resume-related metrics from database"""
        conn = get_database_connection()
        cursor = conn.cursor()
        
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_month = now.replace(day=1)
        metrics = {}
        for period, start_date in [
            ('Today', start_of_day),
            ('This Week', start_of_week),
            ('This Month', start_of_month),
            ('All Time', datetime(2000, 1, 1))
        ]:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_resumes
                FROM resumes
                WHERE created_at >= ?
            """, (start_date.strftime('%Y-%m-%d %H:%M:%S'),))
            
            row = cursor.fetchone()
            if row:
                metrics[period] = {
                    'total': row['total_resumes'] or 0,
                    'ats_score': 0,  
                    'keyword_score': 0,  
                    'high_scoring': 0 
                }
            else:
                metrics[period] = {
                    'total': 0,
                    'ats_score': 0,
                    'keyword_score': 0,
                    'high_scoring': 0
                }
        
        return metrics

    def get_skill_distribution(self):
        """Get skill distribution data"""
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT resume_data FROM resumes")
        resumes = cursor.fetchall()
        
        skill_counts = {}
        for resume in resumes:
            try:
                resume_data = json.loads(resume['resume_data'])
                skills = resume_data.get('skills_categories', {})
                for category, skill_list in skills.items():
                    for skill in skill_list:
                        skill = skill.strip().lower()
                        if skill:
                            skill_category = self._categorize_skill(skill)
                            skill_counts[skill_category] = skill_counts.get(skill_category, 0) + 1
            except json.JSONDecodeError:
                continue
        
        categories = list(skill_counts.keys())
        counts = list(skill_counts.values())

        if not categories:
            categories = ['No Skills']
            counts = [0]
        
        return categories, counts

    def _categorize_skill(self, skill):
        """Helper method to categorize skills"""
        skill = skill.lower()
        if skill in ['python', 'java', 'javascript', 'c++', 'programming']:
            return 'Programming'
        elif skill in ['sql', 'mongodb', 'database']:
            return 'Database'
        elif skill in ['aws', 'azure', 'cloud']:
            return 'Cloud'
        elif skill in ['agile', 'scrum', 'management']:
            return 'Management'
        else:
            return 'Other'

    def get_weekly_trends(self):
        """Get weekly submission trends"""
        conn = get_database_connection()
        cursor = conn.cursor()
        now = datetime.now()
        dates = [(now - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(6, -1, -1)]
        
        submissions = []
        for date in dates:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM resumes 
                WHERE DATE(created_at) = ?
            """, (date,))
            submissions.append(cursor.fetchone()[0])
            
        return [d[-3:] for d in dates], submissions 

    def get_job_category_stats(self):
        """Get statistics by job category"""
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT resume_data FROM resumes")
        resumes = cursor.fetchall()
        
        categories = {}
        for resume in resumes:
            try:
                resume_data = json.loads(resume['resume_data'])
                target_category = resume_data.get('personal_info', {}).get('title', 'Other')
                if not target_category:
                    target_category = resume_data.get('target_category', 'Other')
                categories[target_category] = categories.get(target_category, 0) + 1
            except json.JSONDecodeError:
                continue
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        category_names = [cat[0] for cat in sorted_categories]
        counts = [cat[1] for cat in sorted_categories]
        success_rates = counts  
        if not category_names:
            category_names = ['No Categories']
            success_rates = [0]
            
        return category_names, success_rates

    def get_resume_data(self):
        """Get all resume data"""
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, email, resume_data, created_at FROM resumes ORDER BY created_at DESC")
        return cursor.fetchall()

    def export_to_excel(self, df):
        """Export DataFrame to Excel format"""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Resume Data', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Resume Data']
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            for i, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(str(col))
                ) + 2
                worksheet.set_column(i, i, min(max_length, 50))
        output.seek(0)
        return output.getvalue()

    def get_database_stats(self):
        """Get database statistics"""
        conn = get_database_connection()
        cursor = conn.cursor()
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM resumes")
        stats['total_resumes'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM resumes WHERE DATE(created_at) = DATE('now')")
        stats['today_submissions'] = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        size_bytes = page_count * page_size
        
        if size_bytes < 1024:
            stats['storage_size'] = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            stats['storage_size'] = f"{size_bytes/1024:.1f} KB"
        else:
            stats['storage_size'] = f"{size_bytes/(1024*1024):.1f} MB"
        
        return stats

    def render_dashboard(self):
        metrics = self.get_resume_metrics()
        total_resumes = metrics['All Time']['total']
        avg_ats = 0
        high_performing = 0  
        success_rate = 0  
        trend_indicators = {
            'resumes': {'value': 0, 'icon': '→', 'class': 'trend-neutral'},
            'ats': {'value': 0, 'icon': '→', 'class': 'trend-neutral'},
            'high_performing': {'value': 0, 'icon': '→', 'class': 'trend-neutral'},
            'success_rate': {'value': 0, 'icon': '→', 'class': 'trend-neutral'}
        }
        
        stats = {
            "Total Resumes": f"{total_resumes:,}",
            "Avg ATS Score": f"{avg_ats:.1f}%",
            "High Performing": f"{high_performing:,}",
            "Success Rate": f"{success_rate:.1f}%"
        }

        metric_cards = [
            self.components.render_metric_card(
                "Total Resumes", stats['Total Resumes'],
                trend=trend_indicators['resumes']['icon'],
                trend_value=trend_indicators['resumes']['value']
            ),
            self.components.render_metric_card(
                "Avg ATS Score", stats['Avg ATS Score'],
                trend=trend_indicators['ats']['icon'],
                trend_value=trend_indicators['ats']['value']
            ),
            self.components.render_metric_card(
                "High Performing", stats['High Performing'],
                trend=trend_indicators['high_performing']['icon'],
                trend_value=trend_indicators['high_performing']['value']
            ),
            self.components.render_metric_card(
                "Success Rate", stats['Success Rate'],
                trend=trend_indicators['success_rate']['icon'],
                trend_value=trend_indicators['success_rate']['value']
            )
        ]

        ats_gauge = self.components.create_gauge_chart(float(avg_ats), "ATS Score Performance", "ats-gauge-chart")
        categories, counts = self.get_skill_distribution()
        skill_distribution = self.components.create_bar_chart(categories, counts, "Skill Distribution", "skill-distribution-chart")
        dates, submissions = self.get_weekly_trends()
        submission_trends = self.components.create_trend_chart(dates, submissions, "Weekly Submission Pattern", "submission-trends-chart")
        job_categories, rates = self.get_job_category_stats()
        job_category_chart = self.components.create_bar_chart(job_categories, rates, "Resumes by Job Category", "job-category-chart")


        resume_data = self.get_resume_data()
        resumes = []
        for resume in resume_data:
            resume_dict = {
                'id': resume['id'],
                'full_name': resume['full_name'],
                'email': resume['email'],
                'resume_data': json.loads(resume['resume_data']),
                'created_at': resume['created_at']
            }
            resumes.append(resume_dict)

        db_stats = self.get_database_stats()

        return {
            'metric_cards': metric_cards,
            'ats_gauge': ats_gauge,
            'skill_distribution': skill_distribution,
            'submission_trends': submission_trends,
            'job_category_chart': job_category_chart,
            'resumes': resumes,
            'db_stats': db_stats,
            'last_updated': datetime.now().strftime('%B %d, %Y %I:%M %p')
        }