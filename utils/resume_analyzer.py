import re
import PyPDF2
import io
from docx import Document

class ResumeAnalyzer:
    def __init__(self):
        self.document_types = {
            'resume': [
                'experience', 'education', 'skills', 'work', 'project', 'objective',
                'summary', 'employment', 'qualification', 'achievements'
            ],
            'marksheet': [
                'grade', 'marks', 'score', 'semester', 'cgpa', 'sgpa', 'examination',
                'result', 'academic year', 'percentage'
            ],
            'certificate': [
                'certificate', 'certification', 'awarded', 'completed', 'achievement',
                'training', 'course completion', 'qualified'
            ],
            'id_card': [
                'id card', 'identity', 'student id', 'employee id', 'valid until',
                'date of issue', 'identification'
            ]
        }
        
    def detect_document_type(self, text):
        text = text.lower()
        scores = {}
        for doc_type, keywords in self.document_types.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            density = matches / len(keywords)
            frequency = matches / (len(text.split()) + 1) 
            scores[doc_type] = (density * 0.7) + (frequency * 0.3)
        best_match = max(scores.items(), key=lambda x: x[1])
        return best_match[0] if best_match[1] > 0.15 else 'unknown'
        
    def calculate_keyword_match(self, resume_text, required_skills):
        resume_text = resume_text.lower()
        found_skills = []
        missing_skills = []
        
        for skill in required_skills:
            skill_lower = skill.lower()
            if skill_lower in resume_text:
                found_skills.append(skill)
            elif any(skill_lower in phrase for phrase in resume_text.split('.')):
                found_skills.append(skill)
            else:
                missing_skills.append(skill)
                
        match_score = (len(found_skills) / len(required_skills)) * 100 if required_skills else 0
        
        return {
            'score': match_score,
            'found_skills': found_skills,
            'missing_skills': missing_skills
        }
        
    def check_resume_sections(self, text):
        text = text.lower()
        essential_sections = {
            'contact': ['email', 'phone', 'address', 'linkedin'],
            'education': ['education', 'university', 'college', 'degree', 'academic'],
            'experience': ['experience', 'work', 'employment', 'job', 'internship'],
            'skills': ['skills', 'technologies', 'tools', 'proficiencies', 'expertise']
        }
        
        section_scores = {}
        for section, keywords in essential_sections.items():
            found = sum(1 for keyword in keywords if keyword in text)
            section_scores[section] = min(25, (found / len(keywords)) * 25)
            
        return sum(section_scores.values())
        
    def check_formatting(self, text):
        lines = text.split('\n')
        score = 100
        deductions = []
        if len(text) < 300:
            score -= 30
            deductions.append("Resume is too short")
        if not any(line.isupper() for line in lines):
            score -= 20
            deductions.append("No clear section headers found")
        if not any(line.strip().startswith(('•', '-', '*', '→')) for line in lines):
            score -= 20
            deductions.append("No bullet points found for listing details")
        if any(len(line.strip()) == 0 and len(next_line.strip()) == 0 
               for line, next_line in zip(lines[:-1], lines[1:])):
            score -= 15
            deductions.append("Inconsistent spacing between sections")
        contact_patterns = [
            r'\b[\w\.-]+@[\w\.-]+\.\w+\b',  
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 
            r'linkedin\.com/\w+',  
        ]
        if not any(re.search(pattern, text) for pattern in contact_patterns):
            score -= 15
            deductions.append("Missing or improperly formatted contact information")
            
        return max(0, score), deductions
        
    def extract_text_from_pdf(self, file):
        try:
            # Ensure the file pointer is at the beginning
            file.seek(0)
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
            
    def extract_text_from_docx(self, docx_file):
        try:
            doc = Document(docx_file)
            full_text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text)
            return '\n'.join(full_text)
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX file: {str(e)}")

    def extract_personal_info(self, text):
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        phone_pattern = r'(\+\d{1,3}[-.]?)?\s*\(?\d{3}\)?[-.]?\s*\d{3}[-.]?\s*\d{4}'
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        github_pattern = r'github\.com/[\w-]+'
        email = re.search(email_pattern, text)
        phone = re.search(phone_pattern, text)
        linkedin = re.search(linkedin_pattern, text)
        github = re.search(github_pattern, text)
        # First non-empty line is likely the name
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        name = lines[0] if lines else 'Unknown'
        
        return {
            'name': name if len(name) > 0 and not re.search(r'^(education|experience|skills|summary|objective)$', name.lower()) else 'Unknown',
            'email': email.group(0) if email else '',
            'phone': phone.group(0) if phone else '',
            'linkedin': linkedin.group(0) if linkedin else '',
            'github': github.group(0) if github else '',
            'portfolio': ''
        }

    def extract_education(self, text):
        education = []
        lines = text.split('\n')
        education_keywords = [
            'education', 'academic', 'qualification', 'degree', 'university', 'college',
            'school', 'institute', 'certification', 'diploma', 'bachelor', 'master',
            'phd', 'b.tech', 'm.tech', 'b.e', 'm.e', 'b.sc', 'm.sc','bca', 'mca', 'b.com',
            'm.com', 'b.cs-it', 'imca', 'bba', 'mba', 'honors', 'scholarship'
        ]
        in_education_section = False
        current_entry = []

        for line in lines:
            line = line.strip()
            if any(keyword.lower() in line.lower() for keyword in education_keywords):
                if not any(keyword.lower() == line.lower() for keyword in education_keywords):
                    current_entry.append(line)
                in_education_section = True
                continue
            
            if in_education_section:
                # Check if we've hit another major section (e.g., Experience, Skills)
                if line and any(keyword.lower() in line.lower() for keyword in self.document_types['resume']):
                    if not any(edu_key.lower() in line.lower() for edu_key in education_keywords):
                        in_education_section = False
                        if current_entry:
                            education.append(' '.join(current_entry))
                            current_entry = []
                        continue
                
                if line:
                    current_entry.append(line)
                elif current_entry:
                    education.append(' '.join(current_entry))
                    current_entry = []
        
        if current_entry:
            education.append(' '.join(current_entry))
        
        return [edu for edu in education if edu]

    def extract_experience(self, text):
        experience = []
        lines = text.split('\n')
        experience_keywords = [
            'experience', 'employment', 'work history', 'professional experience',
            'work experience', 'career history', 'professional background',
            'employment history', 'job history', 'positions held',
            'job title', 'job responsibilities', 'job description', 'job summary'
        ]
        in_experience_section = False
        current_entry = []

        for line in lines:
            line = line.strip()
            if any(keyword.lower() in line.lower() for keyword in experience_keywords):
                if not any(keyword.lower() == line.lower() for keyword in experience_keywords):
                    current_entry.append(line)
                in_experience_section = True
                continue
            
            if in_experience_section:
                if line and any(keyword.lower() in line.lower() for keyword in self.document_types['resume']):
                    if not any(exp_key.lower() in line.lower() for exp_key in experience_keywords):
                        in_experience_section = False
                        if current_entry:
                            experience.append(' '.join(current_entry))
                            current_entry = []
                        continue
                
                if line:
                    current_entry.append(line)
                elif current_entry:
                    experience.append(' '.join(current_entry))
                    current_entry = []
        
        if current_entry:
            experience.append(' '.join(current_entry))
        
        return [exp for exp in experience if exp]

    def extract_projects(self, text):
        projects = []
        lines = text.split('\n')
        project_keywords = [
            'projects', 'personal projects', 'academic projects', 'key projects',
            'major projects', 'professional projects', 'project experience',
            'relevant projects', 'featured projects','latest projects',
            'top projects'
        ]
        in_project_section = False
        current_entry = []

        for line in lines:
            line = line.strip()
            if any(keyword.lower() in line.lower() for keyword in project_keywords):
                if not any(keyword.lower() == line.lower() for keyword in project_keywords):
                    current_entry.append(line)
                in_project_section = True
                continue
            
            if in_project_section:
                if line and any(keyword.lower() in line.lower() for keyword in self.document_types['resume']):
                    if not any(proj_key.lower() in line.lower() for proj_key in project_keywords):
                        in_project_section = False
                        if current_entry:
                            projects.append(' '.join(current_entry))
                            current_entry = []
                        continue
                
                if line:
                    current_entry.append(line)
                elif current_entry:
                    projects.append(' '.join(current_entry))
                    current_entry = []
        
        if current_entry:
            projects.append(' '.join(current_entry))
        
        return [proj for proj in projects if proj]

    def extract_skills(self, text):
        skills = set()
        lines = text.split('\n')
        skills_keywords = [
            'skills', 'technical skills', 'competencies', 'expertise',
            'core competencies', 'professional skills', 'key skills',
            'technical expertise', 'proficiencies', 'qualifications',
            'top skills', 'key skill', 'major skill', 'personal skill',
            'soft skills', 'soft skill', 'soft skillset'
        ]
        in_skills_section = False
        current_entry = []

        separators = [',', '•', '|', '/', '\\', '·', '>', '-', '–', '―']

        for line in lines:
            line = line.strip()
            if any(keyword.lower() in line.lower() for keyword in skills_keywords):
                if not any(keyword.lower() == line.lower() for keyword in skills_keywords):
                    current_entry.append(line)
                in_skills_section = True
                continue
            
            if in_skills_section:
                if line and any(keyword.lower() in line.lower() for keyword in self.document_types['resume']):
                    if not any(skill_key.lower() in line.lower() for skill_key in skills_keywords):
                        in_skills_section = False
                        if current_entry:
                            text_to_process = ' '.join(current_entry)
                            for separator in separators:
                                if separator in text_to_process:
                                    skills.update(skill.strip() for skill in text_to_process.split(separator) if skill.strip())
                            current_entry = []
                        continue
                
                if line:
                    current_entry.append(line)
                elif current_entry:
                    text_to_process = ' '.join(current_entry)
                    for separator in separators:
                        if separator in text_to_process:
                            skills.update(skill.strip() for skill in text_to_process.split(separator) if skill.strip())
                    current_entry = []
        
        if current_entry:
            text_to_process = ' '.join(current_entry)
            for separator in separators:
                if separator in text_to_process:
                    skills.update(skill.strip() for skill in text_to_process.split(separator) if skill.strip())
        
        return list(skills)

    def extract_summary(self, text):
        summary = []
        lines = text.split('\n')
        summary_keywords = [
            'summary', 'professional summary', 'career summary', 'objective',
            'career objective', 'professional objective', 'about me', 'profile',
            'professional profile', 'career profile', 'overview', 'skill summary'
        ]
        in_summary_section = False
        current_entry = []

        # Check the first few non-empty lines for a potential summary
        start_index = 0
        while start_index < min(10, len(lines)) and not lines[start_index].strip():
            start_index += 1

        first_lines = []
        lines_checked = 0
        for line in lines[start_index:]:
            if line.strip():
                first_lines.append(line.strip())
                lines_checked += 1
                if lines_checked >= 5:
                    break

        if first_lines and not any(keyword in first_lines[0].lower() for keyword in summary_keywords):
            potential_summary = ' '.join(first_lines)
            if len(potential_summary.split()) > 10:
                if not re.search(r'\b(?:email|phone|address|tel|mobile|linkedin)\b', potential_summary.lower()):
                    summary.append(potential_summary)

        for line in lines:
            line = line.strip()
            if any(keyword.lower() in line.lower() for keyword in summary_keywords):
                if not any(keyword.lower() == line.lower() for keyword in summary_keywords):
                    current_entry.append(line)
                in_summary_section = True
                continue
            
            if in_summary_section:
                if line and any(keyword.lower() in line.lower() for keyword in self.document_types['resume']):
                    if not any(sum_key.lower() in line.lower() for sum_key in summary_keywords):
                        in_summary_section = False
                        if current_entry:
                            summary.append(' '.join(current_entry))
                            current_entry = []
                        continue
                
                if line:
                    current_entry.append(line)
                elif current_entry:
                    summary.append(' '.join(current_entry))
                    current_entry = []
        
        if current_entry:
            summary.append(' '.join(current_entry))
        
        return ' '.join(summary) if summary else ''

    def analyze_resume(self, resume_data, job_requirements):
        text = resume_data.get('raw_text', '')
        if not text:
            return {
                'ats_score': 0,
                'document_type': 'unknown',
                'keyword_match': {'score': 0, 'found_skills': [], 'missing_skills': []},
                'section_score': 0,
                'format_score': 0,
                'suggestions': ["No text provided for analysis. Please upload a valid resume."]
            }
            
        personal_info = self.extract_personal_info(text)
        
        doc_type = self.detect_document_type(text)
        if doc_type != 'resume':
            return {
                'ats_score': 0,
                'document_type': doc_type,
                'keyword_match': {'score': 0, 'found_skills': [], 'missing_skills': []},
                'section_score': 0,
                'format_score': 0,
                'suggestions': [f"This appears to be a {doc_type} document. Please upload a resume for ATS analysis."]
            }
            
        required_skills = job_requirements.get('required_skills', [])
        keyword_match = self.calculate_keyword_match(text, required_skills)
        
        education = self.extract_education(text)
        experience = self.extract_experience(text)
        projects = self.extract_projects(text)
        skills = self.extract_skills(text)
        summary = self.extract_summary(text)
        
        section_score = self.check_resume_sections(text)
        
        format_score, format_deductions = self.check_formatting(text)
        
        contact_suggestions = []
        if not personal_info.get('email'):
            contact_suggestions.append("Add your email address")
        if not personal_info.get('phone'):
            contact_suggestions.append("Add your phone number")
        if not personal_info.get('linkedin'):
            contact_suggestions.append("Add your LinkedIn profile URL")
        
        summary_suggestions = []
        if not summary:
            summary_suggestions.append("Add a professional summary to highlight your key qualifications")
        elif len(summary.split()) < 30:
            summary_suggestions.append("Expand your professional summary to better highlight your experience and goals")
        elif len(summary.split()) > 100:
            summary_suggestions.append("Consider making your summary more concise (aim for 50-75 words)")
        
        skills_suggestions = []
        if not skills:
            skills_suggestions.append("Add a dedicated skills section")
        if len(skills) < 5:
            skills_suggestions.append("List more relevant technical and soft skills")
        if keyword_match['score'] < 70:
            skills_suggestions.append("Add more skills that match the job requirements")
        
        experience_suggestions = []
        if not experience:
            experience_suggestions.append("Add your work experience section")
        else:
            has_dates = any(re.search(r'\b(19|20)\d{2}\b', exp) for exp in experience)
            has_bullets = any(re.search(r'[•\-\*]', exp) for exp in experience)
            has_action_verbs = any(re.search(r'\b(developed|managed|created|implemented|designed|led|improved)\b', 
                                           exp.lower()) for exp in experience)
            
            if not has_dates:
                experience_suggestions.append("Include dates for each work experience")
            if not has_bullets:
                experience_suggestions.append("Use bullet points to list your achievements and responsibilities")
            if not has_action_verbs:
                experience_suggestions.append("Start bullet points with strong action verbs")
        
        education_suggestions = []
        if not education:
            education_suggestions.append("Add your educational background")
        else:
            has_dates = any(re.search(r'\b(19|20)\d{2}\b', edu) for edu in education)
            has_degree = any(re.search(r'\b(bachelor|master|phd|b\.|m\.|diploma)\b', 
                                     edu.lower()) for edu in education)
            has_gpa = any(re.search(r'\b(gpa|cgpa|grade|percentage)\b', 
                                  edu.lower()) for edu in education)
            
            if not has_dates:
                education_suggestions.append("Include graduation dates")
            if not has_degree:
                education_suggestions.append("Specify your degree type")
            if not has_gpa and job_requirements.get('require_gpa', False):
                education_suggestions.append("Include your GPA if it's above 3.0")
        
        format_suggestions = format_deductions
        
        contact_score = 100 - (len(contact_suggestions) * 25)
        summary_score = 100 - (len(summary_suggestions) * 33)
        skills_score = keyword_match['score']
        experience_score = 100 - (len(experience_suggestions) * 25)
        education_score = 100 - (len(education_suggestions) * 25)
        
        ats_score = (
            int(round(contact_score * 0.1)) +
            int(round(summary_score * 0.1)) +
            int(round(skills_score * 0.3)) +
            int(round(experience_score * 0.2)) +
            int(round(education_score * 0.1)) +
            int(round(format_score * 0.2))
        )
        
        suggestions = []
        suggestions.extend(contact_suggestions)
        suggestions.extend(summary_suggestions)
        suggestions.extend(skills_suggestions)
        suggestions.extend(experience_suggestions)
        suggestions.extend(education_suggestions)
        suggestions.extend(format_suggestions)
        
        if not suggestions:
            suggestions.append("Your resume is well-optimized for ATS systems")
        
        return {
            **personal_info,
            'ats_score': ats_score,
            'document_type': 'resume',
            'keyword_match': keyword_match,
            'section_score': section_score,
            'format_score': format_score,
            'education': education,
            'experience': experience,
            'projects': projects,
            'skills': skills,
            'summary': summary,
            'suggestions': suggestions,
            'contact_suggestions': contact_suggestions,
            'summary_suggestions': summary_suggestions,
            'skills_suggestions': skills_suggestions,
            'experience_suggestions': experience_suggestions,
            'education_suggestions': education_suggestions,
            'format_suggestions': format_suggestions,
            'section_scores': {
                'contact': contact_score,
                'summary': summary_score,
                'skills': skills_score,
                'experience': experience_score,
                'education': education_score,
                'format': format_score
            }
        }