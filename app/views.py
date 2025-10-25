from django.shortcuts import render, redirect
from .models import Rubric, Student, Progress
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Avg
from datetime import datetime, timedelta
import json
import google.generativeai as genai
from django.conf import settings
from docx import Document
from PyPDF2 import PdfReader
import io

# Configure Gemini client once
genai.configure(api_key=settings.GOOGLE_API_KEY)

def grade_assignment(request):
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    student = request.POST.get('student', '').strip()
    rubric_id = request.POST.get('rubric', '').strip()
    rubric = Rubric.objects.get(id=rubric_id)
    strictness = rubric.strictness
    grade_level = rubric.grade_level

    # Handle file upload if present
    if 'assignment_file' in request.FILES:
        file = request.FILES['assignment_file']
        
        # Check file type
        if file.name.endswith('.docx'):
            # Handle Word document
            doc = Document(io.BytesIO(file.read()))
            description = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif file.name.endswith('.pdf'):
            # Handle PDF files
            pdf = PdfReader(io.BytesIO(file.read()))
            text_content = []
            for page in pdf.pages:
                text_content.append(page.extract_text())
            description = '\n'.join(text_content)
        elif file.name.endswith('.txt'):
            # Handle text files
            description = file.read().decode('utf-8')
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Unsupported file type. Please upload .txt, .docx, or .pdf files only.'
            }, status=400)
    else:
        description = request.POST.get('description', '').strip()

    prompt_score = f""" 
    Strictness rating (How strict you should grade this student's assignment): {strictness}
    Grade Level (The educational level of the student): {grade_level}
    Rubric (The criteria of which you will be grading the assignment): {rubric.description}
    Student's Assignment (The work that you will be grading): {description}

    You are a teacher grading an assignment, with a strictness rating of {strictness} / 10. Grade this students assignment with the 
    following rubric and only output with this format. i want the only thing you tell me to be the score on this JSON format: {{
            "total_score": number,
            "percentage": number,
            "feedback_summary": string,
            "rubric_breakdown": [
                {{
                    "criterion": string,
                    "score": number,
                    "feedback": string
                }}
            ]
        }}"""

    assignment_score = model.generate_content(prompt_score).text
    
    # Clean the response - remove markdown code blocks
    if assignment_score.startswith('```json'):
        assignment_score = assignment_score.replace('```json', '').replace('```', '').strip()
    elif assignment_score.startswith('```'):
        assignment_score = assignment_score.replace('```', '').strip()
    
    try:
        score_data = json.loads(assignment_score)
        
        total_score = score_data.get('total_score')
        feedback_summary = score_data.get('feedback_summary')
        rubric_breakdown = score_data.get('rubric_breakdown', [])
        percentage = score_data.get('percentage')
        
        # Get student and rubric objects for context
        student_obj = Student.objects.get(id=student)
        # Prepare context for template
        context = {
            'student': student_obj,
            'rubric': rubric,
            'assignment_description': description,
            'total_score': total_score,
            'feedback_summary': feedback_summary,
            'rubric_breakdown': rubric_breakdown,
            'strictness': strictness,
            'grade_level': grade_level
        }
        Progress.objects.create(
            student=student_obj,
            rubric=rubric,
            score=percentage
        )
        return render(request, 'app/grade_result.html', context)
            
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {assignment_score}")
        return redirect('dashboard')

# Create your views here.
def home(request):
    if request.user.is_authenticated:
        return render(request, 'app/home_logged.html')
    else:
        return render(request, 'app/home.html')
def dashboard(request):
    print(request.user)
    try:
        rubrics = Rubric.objects.filter(user = request.user)
        students = Student.objects.filter(user = request.user)
    except Exception as e:
        rubrics = []
        students = []    
        print(e)
    
    context = {
        'rubrics': rubrics,
        'students': students
    }
    return render(request, 'app/dashboard.html', context)
@login_required
@require_http_methods(["POST"]) 
def create_rubric(request):
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    strictness = request.POST.get('strictness', '').strip()
    grade = request.POST.get('grade-level', '').strip()
    print('grade level:', grade)
    if not title:
        rubrics = Rubric.objects.all()
        context = {
            'rubrics': rubrics,
            'error': 'Title is required.'
        }
        return render(request, 'app/dashboard.html', context, status=400)

    Rubric.objects.create(title=title, description=description, strictness=strictness , grade_level=grade, user = request.user)
    return redirect('dashboard')

def progress(request):
    rubrics = Rubric.objects.filter(user=request.user)
    students = Student.objects.filter(user=request.user)
    
    subjects_data = {}
    subject_choices = [
        ('Math', 'Math'),
        ('Science', 'Science'),
        ('English', 'English'),
        ('History', 'History'),
        ('Geography', 'Geography'),
        ('Art', 'Art'),
        ('Music', 'Music'),
    ]
    
    for subject_choice in subject_choices:
        subject = subject_choice[0]
        subject_rubrics = rubrics.filter(subject=subject)
        
        if subject_rubrics.exists():
            # Get all progress data ordered by creation date
            progress_data = Progress.objects.filter(
                rubric__subject=subject
            ).order_by('created_at')
            
            # Get all assignments in order
            assignments = progress_data.values_list('created_at', 'rubric__title')
            labels = [f"{rubric_title} ({created_at.strftime('%Y-%m-%d %H:%M')})" 
                     for created_at, rubric_title in assignments]
            
            # Get all students who have progress in this subject
            subject_students = Student.objects.filter(progress__rubric__subject=subject).distinct()
            
            # Individual student data
            individual_data = {}
            for student in subject_students:
                student_scores = progress_data.filter(student=student).values_list('score', flat=True)
                individual_data[student.name] = {
                    'id': student.id,
                    'data': list(student_scores)  # Convert scores to list
                }
            
            # Class average data
            class_scores = []
            for assignment in assignments:
                avg_score = progress_data.filter(
                    created_at=assignment[0]
                ).aggregate(avg_score=Avg('score'))['avg_score']
                
                class_scores.append(round(avg_score, 1) if avg_score else None)
            
            subjects_data[subject] = {
                'labels': labels,
                'individual': individual_data,
                'class_average': {
                    'label': 'Class Average',
                    'data': class_scores,
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.1)',
                    'tension': 0.4,
                    'fill': False
                }
            }
    
    students_data = [{'id': s.id, 'name': s.name} for s in students]
    context = {
        'subjects_data': json.dumps(subjects_data),
        'students_json': json.dumps(students_data),
        'rubrics': rubrics,
        'students': students
    }
    return render(request, 'app/progress.html', context)


def add_student(request):
    name = request.POST.get('name', '').strip()
    print(name)
    print(request.POST)
    Student.objects.create(name=name ,user = request.user)
    print(Student.objects.all())
    return redirect('dashboard')

def delete_rubric(request, rubric_id):
    try:
        rubric = Rubric.objects.get(id=rubric_id)
        rubric.delete()
        return JsonResponse({'status': 'success'})
    except Rubric.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Rubric not found'}, status=404)
    
def edit_rubric(request, rubric_id):
    rubric = Rubric.objects.get(id=rubric_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        strictness = request.POST.get('strictness', '').strip()
        grade = request.POST.get('grade-level', '').strip()
        
        rubric.title = title
        rubric.description = description
        rubric.strictness = strictness
        rubric.grade_level = grade
        rubric.save()
        
        return redirect('dashboard')
    
    context = {
        'rubric': rubric
    }
    return redirect('dashboard')