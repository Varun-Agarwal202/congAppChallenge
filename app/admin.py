from django.contrib import admin

# Register your models here.
from .models import Rubric, Student, Progress

admin.site.register(Rubric)
admin.site.register(Student)
admin.site.register(Progress)

