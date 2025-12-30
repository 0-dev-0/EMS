from django.shortcuts import render
from django.views import View
from requests import request
from .models import Employee, Attendance, LeaveRequest, Holiday
from django.shortcuts import get_object_or_404, redirect
from .utils import calculate_attendance_percentage
from datetime import date, timedelta
from .views.employee_views import *
from .views.hr_views import *


def home(request):
    return render(request, 'base.html')

class EmployeeListView(View):
    def get(self, request):
        employees = Employee.objects.all()
        return render(request, 'employee/employee_list.html', {'employees': employees})

class AttendanceSummaryView(View):
    def get(self, request):
        data = []

        for emp in Employee.objects.all():
            data.append({
                'employee': emp,
                'attendance_percent': calculate_attendance_percentage(emp)
            })

        return render(
            request,
            'employee/attendance_summary.html',
            {'data': data}
        )

    
class LeaveRequestListView(View):
    def get(self, request):
        leave_requests = LeaveRequest.objects.all()
        return render(request, 'employee/leave_request_list.html', {'leave_requests': leave_requests})
    
class EmployeeDetailView(View):
    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        return render(request, 'employee/employee_detail.html', {'employee': employee})
    
class AttendanceDetailView(View):
    def get(self, request, employee_id):
        employee = get_object_or_404(Employee, id=employee_id)

        start_date = employee.date_hired
        end_date = date.today()

        # Existing attendance records
        records = Attendance.objects.filter(
            employee=employee,
            date__range=(start_date, end_date)
        )
        record_map = {r.date: r for r in records}

        # Holidays
        holidays = set(
            Holiday.objects.filter(
                date__range=(start_date, end_date)
            ).values_list('date', flat=True)
        )

        attendance_days = []

        current = start_date
        while current <= end_date:

            # Skip Saturday (5) & Sunday (6)
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            # Skip holidays
            if current in holidays:
                attendance_days.append({
                    'date': current,
                    'status': 'Holiday',
                    'attendance': None
                })
                current += timedelta(days=1)
                continue

            attendance = record_map.get(current)

            attendance_days.append({
                'date': current,
                'status': attendance.status if attendance else 'Absent',
                'attendance': attendance
            })

            current += timedelta(days=1)

        context = {
            'employee': employee,
            'attendance_days': attendance_days,
            'attendance_percent': calculate_attendance_percentage(employee)
        }

        return render(
            request,
            'employee/attendance_detail.html',
            context
        )

    
class UpdateAttendanceView(View):
    def get(self, request, employee_id, date):
        employee = get_object_or_404(Employee, id=employee_id)
        attendance, _ = Attendance.objects.get_or_create(
            employee=employee,
            date=date,
            defaults={'status': 'Absent'}
        )

        is_holiday = Holiday.objects.filter(date=date).exists()

        return render(request, 'employee/update_attendance.html', {
            'attendance': attendance,
            'status_choices': Attendance._meta.get_field('status').choices,
            'is_holiday': is_holiday
        })

    def post(self, request, employee_id, date):
        attendance = get_object_or_404(
            Attendance,
            employee_id=employee_id,
            date=date
        )

        status = request.POST.get('status')

        if status == 'Holiday':
            Holiday.objects.get_or_create(date=date, name="Manual Holiday")
            attendance.delete()
        else:
            attendance.status = status
            attendance.save()

        return redirect('attendance_detail', employee_id=employee_id)

    
class LeaveRequestDetailView(View):
    def get(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        return render(request, 'employee/leave_request_detail.html', {
            'leave': leave
        })

    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        action = request.POST.get('action')

        if action == 'approve':
            leave.status = 'Approved'
            leave.save()

            # Mark attendance as Leave
            current = leave.start_date
            while current <= leave.end_date:
                Attendance.objects.update_or_create(
                    employee=leave.employee,
                    date=current,
                    defaults={'status': 'Leave'}
                )
                current += timedelta(days=1)

        elif action == 'reject':
            leave.status = 'Rejected'
            leave.save()

        return redirect('leave_request_list')


class DashboardView(View):
    def get(self, request):
        total_employees = Employee.objects.count()
        total_attendance = Attendance.objects.count()
        total_leave_requests = LeaveRequest.objects.count()
        context = {
            'total_employees': total_employees,
            'total_attendance': total_attendance,
            'total_leave_requests': total_leave_requests,
        }
        return render(request, 'employee/dashboard.html', context)


class create_employee(View):
    def get(self, request):
        return render(request, 'employee/create_employee.html')

    def post(self, request):
        Employee.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            position=request.POST.get('position'),
            department=request.POST.get('department'),
            date_hired=request.POST.get('date_hired'),
        )
        return redirect('employee_list')

class delete_employee(View):
    def post(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        employee.delete()
        return redirect('employee_list')
    
class update_employee(View):
    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        return render(request, 'employee/update_employee.html', {
            'employee': employee
        })

    def post(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        employee.first_name = request.POST.get('first_name')
        employee.last_name = request.POST.get('last_name')
        employee.email = request.POST.get('email')
        employee.position = request.POST.get('position')
        employee.department = request.POST.get('department')
        employee.date_hired = request.POST.get('date_hired')
        employee.save()
        return redirect('employee_detail', pk=pk)
    
class DeleteAttendanceView(View):
    def post(self, request, pk):
        Attendance.objects.filter(pk=pk).delete()
        return redirect('attendance_list')

class CreateLeaveRequestView(View):
    def get(self, request):
        employees = Employee.objects.all()
        return render(request, 'employee/create_leave_request.html', {
            'employees': employees
        })

    def post(self, request):
        LeaveRequest.objects.create(
            employee_id=request.POST.get('employee'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            reason=request.POST.get('reason')
        )
        return redirect('leave_request_list')
    
class DeleteLeaveRequestView(View):
    def post(self, request, pk):
        LeaveRequest.objects.filter(pk=pk).delete()
        return redirect('leave_request_list')

@employee_required
def employee_dashboard(request):
    ...
@employee_required
def my_attendance(request):
    ...
@employee_required
def apply_leave(request):
    ...

@hr_required
def hr_dashboard(request):
    ...

@hr_required
def employee_list(request):
    ...
@hr_required
def approve_leave(request):
    ...