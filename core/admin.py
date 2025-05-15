from django.contrib import admin
from .models import Employee, Attendance

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'position')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name')
    list_filter = ('department', 'position')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in', 'check_out', 'status')
    search_fields = ('employee__user__username', 'employee__employee_id')
    list_filter = ('date', 'status')
