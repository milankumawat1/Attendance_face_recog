from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance-history/', views.attendance_history, name='attendance_history'),
    path('register-employee/', views.register_employee, name='register_employee'),
] 