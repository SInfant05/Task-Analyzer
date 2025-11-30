# tasks/urls.py
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('analyze/', views.analyze_tasks_view, name='analyze'),
    path('suggest/', views.suggest_tasks_view, name='suggest'),
]