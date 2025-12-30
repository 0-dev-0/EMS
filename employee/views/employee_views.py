from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from datetime import date, timedelta

from ..models import Employee, Attendance, LeaveRequest, Holiday
from ..utils import calculate_attendance_percentage, employee_required


@employee_required
class EmployeeDashboardView(View):
    def get(self, request):
        employee = request.user.employee

        context = {
            'attendance_percent': calculate_attendance_percentage(employee),
            'leave_count': LeaveRequest.objects.filter(employee=employee).count(),
        }
        return render(request, 'employee/dashboard.html', context)


@employee_required
class MyAttendanceView(View):
    def get(self, request):
        employee = request.user.employee

        start_date = employee.date_hired
        end_date = date.today()

        records = Attendance.objects.filter(
            employee=employee,
            date__range=(start_date, end_date)
        )
        record_map = {r.date: r for r in records}

        holidays = set(
            Holiday.objects.filter(
                date__range=(start_date, end_date)
            ).values_list('date', flat=True)
        )

        attendance_days = []
        current = start_date

        while current <= end_date:
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            if current in holidays:
                attendance_days.append({
                    'date': current,
                    'status': 'Holiday'
                })
            else:
                attendance = record_map.get(current)
                attendance_days.append({
                    'date': current,
                    'status': attendance.status if attendance else 'Absent'
                })

            current += timedelta(days=1)

        return render(request, 'employee/my_attendance.html', {
            'attendance_days': attendance_days,
            'attendance_percent': calculate_attendance_percentage(employee)
        })


@employee_required
class MyLeaveRequestsView(View):
    def get(self, request):
        leaves = LeaveRequest.objects.filter(employee=request.user.employee)
        return render(request, 'employee/my_leave_requests.html', {
            'leaves': leaves
        })


@employee_required
class ApplyLeaveView(View):
    def get(self, request):
        return render(request, 'employee/apply_leave.html')

    def post(self, request):
        LeaveRequest.objects.create(
            employee=request.user.employee,
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            reason=request.POST.get('reason')
        )
        return redirect('my_leave_requests')

@employee_required
class MyProfileView(View):
    def get(self, request):
        return render(request, 'employee/my_profile.html', {
            'employee': request.user.employee
        })
    
@employee_required
class EditMyProfileView(View):
    def get(self, request):
        return render(request, 'employee/edit_profile.html', {
            'employee': request.user.employee
        })

    def post(self, request):
        emp = request.user.employee
        emp.first_name = request.POST.get('first_name')
        emp.last_name = request.POST.get('last_name')
        emp.save()
        return redirect('my_profile')
