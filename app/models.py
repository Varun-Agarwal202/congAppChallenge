from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# Create your models here.
class Rubric(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subject = models.CharField(max_length=200, choices=[
        ('Math', 'Math'),
        ('Science', 'Science'),
        ('English', 'English'),
        ('History', 'History'),
        ('Geography', 'Geography'),
        ('Art', 'Art'),
        ('Music', 'Music'),
    ], default='Math')
    grade_level = models.CharField(max_length=50 , default='Grade 1')
    strictness = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    training_data = models.JSONField(null = True)
    def __str__(self):
        return self.title
    
class Student(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    def __str__(self):
        return self.name
    
class Progress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    evaluate = models.CharField(max_length = 50, null = True)
    def __str__(self):
        return f"{self.student.name} - {self.rubric.title}"