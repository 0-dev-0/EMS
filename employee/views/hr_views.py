from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from datetime import timedelta

from ..models import Employee, Attendance, LeaveRequest
from ..utils import calculate_attendance_percentage, hr_required


@hr_required
class HRDashboardView(View):
    def get(self, request):
        context = {
            'total_employees': Employee.objects.count(),
            'total_attendance': Attendance.objects.count(),
            'total_leave_requests': LeaveRequest.objects.count(),
        }
        return render(request, 'hr/dashboard.html', context)


@hr_required
class EmployeeListView(View):
    def get(self, request):
        employees = Employee.objects.all()
        return render(request, 'hr/employee_list.html', {
            'employees': employees
        })


@hr_required
class EmployeeDetailView(View):
    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        return render(request, 'hr/employee_detail.html', {
            'employee': employee,
            'attendance_percent': calculate_attendance_percentage(employee)
        })


@hr_required
class CreateEmployeeView(View):
    def get(self, request):
        return render(request, 'hr/create_employee.html')

    def post(self, request):
        Employee.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            position=request.POST.get('position'),
            department=request.POST.get('department'),
            date_hired=request.POST.get('date_hired'),
        )
        return redirect('hr_employee_list')


@hr_required
class UpdateEmployeeView(View):
    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        return render(request, 'hr/update_employee.html', {'employee': employee})

    def post(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        employee.first_name = request.POST.get('first_name')
        employee.last_name = request.POST.get('last_name')
        employee.email = request.POST.get('email')
        employee.position = request.POST.get('position')
        employee.department = request.POST.get('department')
        employee.date_hired = request.POST.get('date_hired')
        employee.save()
        return redirect('hr_employee_detail', pk=pk)


@hr_required
class DeleteEmployeeView(View):
    def post(self, request, pk):
        Employee.objects.filter(pk=pk).delete()
        return redirect('hr_employee_list')


@hr_required
class LeaveApprovalView(View):
    def get(self, request):
        leaves = LeaveRequest.objects.filter(status='Pending')
        return render(request, 'hr/leave_approvals.html', {
            'leaves': leaves
        })

    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        action = request.POST.get('action')

        if action == 'approve':
            leave.status = 'Approved'
            leave.save()

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

        return redirect('hr_leave_approvals')