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

# Configure Gemini client once
genai.configure(api_key=settings.GOOGLE_API_KEY)

def grade_assignment(request):
    model = genai.GenerativeModel("gemini-2.5-flash")
    student = request.POST.get('student', '').strip()
    rubric_id = request.POST.get('rubric', '').strip()
    description  = request.POST.get('description', '').strip()
    rubric = Rubric.objects.get(id=rubric_id)
    strictness = rubric.strictness
    grade_level = rubric.grade_level
    print(grade_level)

    prompt_score = f""" 
    Strictness rating (How strict you should grade this student's assignment): {strictness}
    Grade Level (The educational level of the student): {grade_level}
    Rubric (The criteria of which you will be grading the assignment): {rubric.description}
    Student's Assignment (The work that you will be grading): {description}

    You are a teacher grading an assignment, with a strictness rating of {strictness} / 10. Grade this students assignment with the 
    following rubric and only output with this format. i want the only thing you tell me to be the score on this JSON format: {{
            "total_score": number,
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
    rubrics = Rubric.objects.all()
    students = Student.objects.all()
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

    Rubric.objects.create(title=title, description=description, strictness=strictness , grade_level=grade)
    return redirect('dashboard')

def progress(request):
    rubrics = Rubric.objects.all()
    students = Student.objects.all()
    
    # Get all subjects with their progress data
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
            # Get progress data for the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            progress_data = Progress.objects.filter(
                rubric__subject=subject,
                created_at__gte=thirty_days_ago
            ).order_by('created_at')
            
            # Get unique dates for labels
            dates = progress_data.values_list('created_at__date', flat=True).distinct().order_by('created_at__date')
            labels = [str(date) for date in dates]
            
            # Get all students who have progress in this subject
            subject_students = Student.objects.filter(progress__rubric__subject=subject).distinct()
            
            # Individual student data
            individual_data = {}
            for student in subject_students:
                student_data = []
                for date in dates:
                    # Get average score for this student on this date for this subject
                    avg_score = progress_data.filter(
                        student=student,
                        created_at__date=date
                    ).aggregate(avg_score=Avg('score'))['avg_score']
                    
                    student_data.append(round(avg_score, 1) if avg_score else None)
                
                individual_data[student.name] = {
                    'id': student.id,
                    'data': student_data
                }
            
            # Class average data
            class_average_data = []
            for date in dates:
                # Get average score for all students on this date for this subject
                avg_score = progress_data.filter(
                    created_at__date=date
                ).aggregate(avg_score=Avg('score'))['avg_score']
                
                class_average_data.append(round(avg_score, 1) if avg_score else None)
            
            subjects_data[subject] = {
                'labels': labels,
                'individual': individual_data,
                'class_average': {
                    'label': 'Class Average',
                    'data': class_average_data,
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.1)',
                    'tension': 0.4,
                    'fill': False
                }
            }
    
    context = {
        'rubrics': rubrics,
        'students': students,
        'subjects_data': json.dumps(subjects_data),
        'students_json': json.dumps([{'id': s.id, 'name': s.name} for s in students])
    }
    return render(request, 'app/progress.html', context)


def add_student(request):
    name = request.POST.get('name', '').strip()
    print(name)
    print(request.POST)
    Student.objects.create(name=name)
    print(Student.objects.all())
    return redirect('dashboard')