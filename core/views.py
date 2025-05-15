from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, Http404
from .models import Employee, Attendance, EmployeeFace
from django.utils import timezone
import cv2
import numpy as np
import face_recognition
import json
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods

def handler404(request, exception):
    return render(request, 'core/404.html', status=404)

def handler500(request):
    return render(request, 'core/500.html', status=500)

def is_superuser(user):
    return user.is_superuser

# Create your views here.

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')

def check_face_in_image(image_data):
    try:
        # Read the image
        image_array = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return False, "Failed to decode image"
        
        # Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            return False, "No face detected in the image"
        
        if len(face_locations) > 1:
            return False, "Multiple faces detected. Please ensure only one face is visible"
        
        return True, "Face detected successfully"
    except Exception as e:
        return False, str(e)

@login_required
@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def register_employee(request):
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            employee_id = request.POST.get('employee_id')
            department = request.POST.get('department')
            position = request.POST.get('position')
            
            # Validate required fields
            if not all([username, password, first_name, last_name, email, employee_id, department, position]):
                return JsonResponse({'success': False, 'error': 'All fields are required'})
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Username already exists'})
            
            # Check if employee_id already exists
            if Employee.objects.filter(employee_id=employee_id).exists():
                return JsonResponse({'success': False, 'error': 'Employee ID already exists'})
            
            # Get the image from the request
            image_file = request.FILES.get('image')
            if not image_file:
                return JsonResponse({'success': False, 'error': 'No image provided'})
            
            # Read the image data once
            image_data = image_file.read()
            
            # Check image for face
            success, message = check_face_in_image(image_data)
            if not success:
                return JsonResponse({
                    'success': False,
                    'error': 'Face detection failed',
                    'face_check_result': {'message': message}
                })
            
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            
            try:
                # Create employee
                employee = Employee.objects.create(
                    user=user,
                    employee_id=employee_id,
                    department=department,
                    position=position
                )
                
                # Process image to store face encoding
                image_array = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                face_encodings = face_recognition.face_encodings(rgb_image)
                
                if not face_encodings:
                    raise Exception('No face detected in the image')
                
                # Store face encoding
                EmployeeFace.objects.create(
                    employee=employee,
                    face_encoding=face_encodings[0].tobytes()
                )
                
                messages.success(request, 'Employee registered successfully')
                return JsonResponse({'success': True, 'message': 'Employee registered successfully'})
                
            except Exception as e:
                # Clean up if any error occurs
                if 'employee' in locals():
                    employee.delete()
                user.delete()
                raise e
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'core/register_employee.html')

@login_required
@require_http_methods(["GET", "POST"])
def mark_attendance(request):
    if request.method == 'POST':
        try:
            # Get the image from the request
            image_file = request.FILES.get('image')
            if not image_file:
                return JsonResponse({'success': False, 'error': 'No image provided'})

            # Read the image
            image_array = np.frombuffer(image_file.read(), np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                return JsonResponse({'success': False, 'error': 'Failed to decode image'})
            
            # Convert to RGB (face_recognition uses RGB)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_image)
            if not face_locations:
                return JsonResponse({'success': False, 'error': 'No face detected'})
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            if not face_encodings:
                return JsonResponse({'success': False, 'error': 'Could not encode face'})
            
            # Get all employees with their face encodings
            employees = Employee.objects.all()
            matched_employee = None
            
            # Compare with all stored face encodings
            for employee in employees:
                employee_faces = EmployeeFace.objects.filter(employee=employee)
                for face in employee_faces:
                    stored_encoding = np.frombuffer(face.face_encoding, dtype=np.float64)
                    matches = face_recognition.compare_faces([stored_encoding], face_encodings[0])
                    if matches[0]:
                        matched_employee = employee
                        break
                if matched_employee:
                    break
                
            if not matched_employee:
                return JsonResponse({'success': False, 'error': 'Face not recognized. Please register first.'})
            
            # Mark attendance
            today = timezone.now().date()
            attendance, created = Attendance.objects.get_or_create(
                employee=matched_employee,
                date=today,
                defaults={'check_in': timezone.now()}
            )
            
            if not created:
                if not attendance.check_out:
                    attendance.check_out = timezone.now()
                    attendance.save()
                    return JsonResponse({
                        'success': True,
                        'message': f'Check-out recorded successfully for {matched_employee.user.get_full_name()}'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f'Already checked in and out for today, {matched_employee.user.get_full_name()}'
                    })
            
            return JsonResponse({
                'success': True,
                'message': f'Check-in recorded successfully for {matched_employee.user.get_full_name()}'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'core/mark_attendance.html')

@login_required
@require_http_methods(["GET"])
def attendance_history(request):
    if request.user.is_superuser:
        # Get all employees for the list
        employees = Employee.objects.all().select_related('user')
        today = timezone.now().date()
        
        # Get today's attendance for all employees
        today_attendance = {
            attendance.employee_id: attendance 
            for attendance in Attendance.objects.filter(date=today)
        }
        
        # If an employee_id is provided, show their attendance
        employee_id = request.GET.get('employee_id')
        if employee_id:
            try:
                employee = Employee.objects.get(id=employee_id)
                attendance_records = Attendance.objects.filter(
                    employee=employee
                ).select_related('employee').order_by('-date', '-check_in')
                
                return render(request, 'core/employee_attendance.html', {
                    'employee': employee,
                    'attendance_records': attendance_records
                })
            except Employee.DoesNotExist:
                messages.error(request, 'Employee not found')
                return redirect('core:attendance_history')
        
        # Show list of all employees
        return render(request, 'core/attendance_history.html', {
            'employees': employees,
            'today_attendance': today_attendance,
            'today': today
        })
    else:
        try:
            employee = Employee.objects.get(user=request.user)
            attendance_records = Attendance.objects.filter(
                employee=employee
            ).select_related('employee').order_by('-date', '-check_in')
            
            return render(request, 'core/employee_attendance.html', {
                'employee': employee,
                'attendance_records': attendance_records
            })
        except Employee.DoesNotExist:
            messages.error(request, 'Employee record not found')
            return redirect('core:dashboard')
