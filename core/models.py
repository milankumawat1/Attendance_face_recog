from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"

class EmployeeFace(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='faces')
    face_encoding = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face encoding for {self.employee} - {self.created_at}"

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='present')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.date}"
