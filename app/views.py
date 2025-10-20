from django.shortcuts import render
from .models import Rubric
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
def create_rubric(request):
    pass