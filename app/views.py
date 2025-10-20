from django.shortcuts import render, redirect
from .models import Rubric
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
# Create your views here.
def home(request):
    if request.user.is_authenticated:
        return render(request, 'app/home_logged.html')
    else:
        return render(request, 'app/home.html')
def dashboard(request):
    rubrics = Rubric.objects.all()
    context = {
        'rubrics': rubrics
    }
    return render(request, 'app/dashboard.html', context)
@login_required
@require_http_methods(["POST"]) 
def create_rubric(request):
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()

    if not title:
        rubrics = Rubric.objects.all()
        context = {
            'rubrics': rubrics,
            'error': 'Title is required.'
        }
        return render(request, 'app/dashboard.html', context, status=400)

    Rubric.objects.create(title=title, description=description)
    return redirect('dashboard')