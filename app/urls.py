"""
URL configuration for congAppChallenge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from app.views import home, dashboard, create_rubric, progress, grade_assignment, add_student, delete_rubric, edit_rubric, train_model
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('', home, name='homepage'),
    path('dashboard/', dashboard, name = "dashboard"),
    path('create-rubric/', create_rubric, name="create-rubric"),
    path('progress/', progress, name = "progress"),
    path('grade-assignment/', grade_assignment, name="grade-assignment"),
    path('add-student/', add_student, name="add-student"),
    path('delete-rubric/<int:rubric_id>/', delete_rubric, name="delete-rubric"),
    path('edit-rubric/<int:rubric_id>/', edit_rubric, name="edit-rubric"),
    path('train-model/', train_model, name="train-model"),
]
