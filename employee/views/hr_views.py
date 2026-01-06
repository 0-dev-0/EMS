import calendar
import csv
from datetime import date, timedelta
from django.contrib.auth.models import User, Group
from django.utils.text import slugify
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from requests import request
from django.http import HttpResponse
from urllib.parse import urlencode
from ..forms import HRCreateEmployeeForm
from ..models import Employee, Attendance, LeaveRequest, Holiday
from ..utils import calculate_attendance_percentage, hr_required
from django.db.models import Q


@hr_required
class HRDashboardView(View):
    def get(self, request):
        context = {
            "total_employees": Employee.objects.count(),
            "total_attendance": Attendance.objects.count(),
            "total_leave_requests": LeaveRequest.objects.count(),
        }
        return render(request, "hr/dashboard.html", context)


@hr_required
class EmployeeListView(View):
    def get(self, request):
        employees = Employee.objects.all()
        return render(request, "hr/employee_list.html", {"employees": employees})


@hr_required
class EmployeeDetailView(View):
    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        return render(
            request,
            "hr/employee_detail.html",
            {
                "employee": employee,
                "attendance_percent": calculate_attendance_percentage(employee),
            },
        )


@hr_required
class CreateEmployeeView(View):
    def get(self, request):
        form = HRCreateEmployeeForm()
        return render(request, "hr/create_employee.html", {"form": form})

    def post(self, request):
        form = HRCreateEmployeeForm(request.POST)

        if form.is_valid():
            employee = form.save(commit=False)


            username = request.POST.get("username")

            if not username:
                username = slugify(
                    f"{employee.first_name}.{employee.last_name}"
                )

            user = User.objects.create_user(
                username=username,
                first_name=employee.first_name,
                last_name=employee.last_name,
                email=employee.email,
                password="changeme123"  
            )

            employee.user = user
            employee.save()

            # Add to Employee group
            employee_group, _ = Group.objects.get_or_create(name="Employee")
            user.groups.add(employee_group)

            messages.success(
                request,
                f"Employee created. Username: {username}, Password: changeme123"
            )
            return redirect("employee_list")

        return render(request, "hr/create_employee.html", {"form": form})


@hr_required
class UpdateEmployeeView(View):

    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)

        initial = {}
        if employee.user:
            initial["username"] = employee.user.username

        form = HRCreateEmployeeForm(instance=employee, initial=initial)

        return render(
            request,
            "hr/update_employee.html",
            {
                "employee": employee,
                "form": form
            }
        )

    def post(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        form = HRCreateEmployeeForm(request.POST, instance=employee)

        form_errors = []

        if form.is_valid():
            employee = form.save(commit=False)
            employee.save()

            username = request.POST.get("username", "").strip()

            if employee.user:

                if username:
                    # Ensure username uniqueness
                    if User.objects.exclude(pk=employee.user.pk).filter(username=username).exists():
                        form_errors.append("Username already exists.")
                    else:
                        employee.user.username = username
                else:
                    # Auto-generate username if empty
                    employee.user.username = slugify(
                        f"{employee.first_name}.{employee.last_name}"
                    )

                # Sync user fields
                employee.user.first_name = employee.first_name
                employee.user.last_name = employee.last_name
                employee.user.email = employee.email

                if not form_errors:
                    employee.user.save()
                    messages.success(request, "Employee updated successfully.")
                    return redirect("employee_detail", pk=pk)

            else:
                form_errors.append("No user account linked to this employee.")

        else:
            # Convert Django form errors to readable text
            for field, errors in form.errors.items():
                for error in errors:
                    form_errors.append(error)

        return render(
            request,
            "hr/update_employee.html",
            {
                "employee": employee,
                "form": form,
                "form_errors": form_errors,
            }
        )

@hr_required
class DeleteEmployeeView(View):
    def post(self, request, pk):
        Employee.objects.filter(pk=pk).delete()
        messages.info(request, "Employee deleted.")
        return redirect("employee_list")


@hr_required
class LeaveApprovalView(View):
    def get(self, request):
        leaves = LeaveRequest.objects.filter(status="Pending")
        return render(request, "hr/leave_approvals.html", {"leaves": leaves})

    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        action = request.POST.get("action")

        if action == "approve":
            leave.status = "Approved"
            leave.save()

            current = leave.start_date
            while current <= leave.end_date:
                Attendance.objects.update_or_create(
                    employee=leave.employee,
                    date=current,
                    defaults={"status": "Leave"},
                )
                current += timedelta(days=1)
            messages.success(request, "Leave approved and attendance updated.")

        elif action == "reject":
            leave.status = "Rejected"
            leave.save()
            messages.info(request, "Leave rejected.")

        return redirect("leave_approvals")

@hr_required
class DeleteLeaveRequestView(View):
    def post(self, request, pk):
        LeaveRequest.objects.filter(pk=pk).delete()
        messages.info(request, "Leave request deleted.")
        return redirect("leave_request_list")
    
@hr_required
class LeaveRequestListView(View):
    def get(self, request):
        leave_requests = LeaveRequest.objects.all()
        return render(
            request, "hr/leave_request_list.html", {"leave_requests": leave_requests}
        )
    
@hr_required
class LeaveRequestDetailView(View):
    def get(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        return render(request, "hr/leave_request_detail.html", {"leave": leave})

@hr_required
class AttendanceSummaryView(View):
    def get(self, request):
        employees = Employee.objects.all()
        data = []
        for employee in employees:
            data.append(
                {
                    "employee": employee,
                    "attendance_percent": calculate_attendance_percentage(employee),
                }
            )
        return render(request, "hr/attendance_summary.html", {"data": data})


@hr_required
class AttendanceDetailView(View):
    def get(self, request, employee_id):
        from datetime import date, timedelta
        
        employee = get_object_or_404(Employee, pk=employee_id)
        
        # Get all attendance records for this employee
        attendance_records = {
            record.date: record.status 
            for record in Attendance.objects.filter(employee=employee)
        }
        
        # Get all holidays
        holidays = set(
            Holiday.objects.filter(
                date__gte=employee.date_hired
            ).values_list('date', flat=True)
        )
        
        # Generate all dates from date_hired to today
        all_dates = []
        current_date = employee.date_hired
        today = date.today()
        
        while current_date <= today:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:  # Monday=0 to Friday=4
                # Check if it's a holiday
                if current_date in holidays:
                    status = "Holiday"
                    attendance_obj = None
                else:
                    # Get status from attendance records, default to "Absent"
                    status = attendance_records.get(current_date, "Absent")
                    # Get attendance object if it exists
                    attendance_obj = Attendance.objects.filter(
                        employee=employee, 
                        date=current_date
                    ).first()
                
                all_dates.append({
                    'date': current_date,
                    'status': status,
                    'attendance_obj': attendance_obj,
                })
            
            current_date += timedelta(days=1)
        
        # Sort by date descending (most recent first)
        all_dates.sort(key=lambda x: x['date'], reverse=True)
        
        return render(
            request,
            "hr/attendance_detail.html",
            {
                "employee": employee,
                "attendance_days": all_dates,
                "attendance_percent": calculate_attendance_percentage(employee),
            },
        )


@hr_required
class DeleteAttendanceView(View):
    def post(self, request, pk):
        Attendance.objects.filter(pk=pk).delete()
        messages.info(request, "Attendance record deleted.")
        return redirect("attendance_summary")


@hr_required
class UpdateAttendanceView(View):
    def get(self, request, employee_id, date):
        from datetime import datetime
        
        employee = get_object_or_404(Employee, pk=employee_id)
        # Parse date string to date object
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Get or create attendance record
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=date_obj,
            defaults={'status': 'Absent'}
        )
        
        return render(request, "hr/update_attendance.html", {"attendance": attendance})

    def post(self, request, employee_id, date):
        from datetime import datetime
        
        employee = get_object_or_404(Employee, pk=employee_id)
        # Parse date string to date object
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        
        status = request.POST.get("status")
        if status in dict(Attendance._meta.get_field("status").choices):
            # Get or create attendance record
            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=date_obj,
                defaults={'status': status}
            )
            if not created:
                attendance.status = status
                attendance.save()
            
            messages.success(request, f"Attendance {'created' if created else 'updated'} successfully.")
        return redirect("attendance_detail", employee_id=employee_id)



@hr_required
class ExportDataPageView(View):
    def get(self, request, *args, **kwargs):
        # Get distinct department names from Employee model
        departments = Employee.objects.values_list('department', flat=True).distinct()
        months = [(i, calendar.month_name[i]) for i in range(1, 13)]
        
        # Filters from GET params
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        dept_id = request.GET.get('department')  # department name
        employee_name = request.GET.get('employee_name')
        month = request.GET.get('month')

        employees = Employee.objects.all().order_by('id')
        if dept_id:
            employees = employees.filter(department=dept_id)
        if employee_name:
            employees = employees.filter(first_name__icontains=employee_name) | employees.filter(last_name__icontains=employee_name)
        if month:
            month = int(month)
            year = date.today().year
            start_date = date(year, month, 1)
            end_date = date(year, month, calendar.monthrange(year, month)[1])
        elif start_date and end_date:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
            # Validate that end_date is not earlier than start_date
            if end_date < start_date:
                messages.error(request, "End date cannot be earlier than start date.")
                start_date = None
                end_date = None
        else:
            start_date = None
            end_date = None

        preview = []
        days = []
        days_formatted = []
        if start_date and end_date:
            delta = end_date - start_date
            days = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
            # Format days for display with month and year (e.g., "10 Dec 2025")
            days_formatted = [d.strftime("%d %b %Y") for d in days]

            # Prepare preview data
            today = date.today()
            holidays = set(Holiday.objects.filter(date__range=(start_date, end_date)).values_list('date', flat=True))
            for emp in employees:
                row = {"employee_name": f"{emp.first_name} {emp.last_name}", "statuses": []}
                join_date = emp.date_hired
                attendances = {att.date: att.status for att in Attendance.objects.filter(employee=emp, date__range=(start_date, end_date))}
                for d in days:
                    if d < join_date:
                        row["statuses"].append('')
                    elif d > today:
                        # Future dates show blank, except holidays
                        if d in holidays:
                            row["statuses"].append("Holiday")
                        else:
                            row["statuses"].append('')
                    elif d in holidays:
                        row["statuses"].append("Holiday")
                    elif d.weekday() >= 5:  # Saturday=5, Sunday=6
                        row["statuses"].append("-")
                    elif d in attendances:
                        row["statuses"].append(attendances[d])
                    else:
                        row["statuses"].append("Absent")
                preview.append(row)

        # Build download URL with all filter parameters
        query_params = {}
        if request.GET.get('start_date'):
            query_params['start_date'] = request.GET.get('start_date')
        if request.GET.get('end_date'):
            query_params['end_date'] = request.GET.get('end_date')
        if request.GET.get('department'):
            query_params['department'] = request.GET.get('department')
        if request.GET.get('employee_name'):
            query_params['employee_name'] = request.GET.get('employee_name')
        if request.GET.get('month'):
            query_params['month'] = request.GET.get('month')
        
        download_url = reverse('export_data')
        if query_params:
            download_url += '?' + urlencode(query_params)
        
        context = {
            "departments": departments,
            "months": months,
            "preview": preview,
            "days": days,
            "days_formatted": days_formatted,
            "download_url": download_url
        }
        return render(request, "hr/export_data.html", context)
    
@hr_required
class ExportDataCSVView(View):
    def get(self, request, *args, **kwargs):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        dept_id = request.GET.get('department')  # department name
        employee_name = request.GET.get('employee_name')
        month = request.GET.get('month')

        # Handle month filter (same logic as preview)
        if month:
            month = int(month)
            year = date.today().year
            start_date = date(year, month, 1)
            end_date = date(year, month, calendar.monthrange(year, month)[1])
        elif start_date and end_date:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
            # Validate that end_date is not earlier than start_date
            if end_date < start_date:
                return HttpResponse("Error: End date cannot be earlier than start date.", status=400)
        else:
            start_date = date.today().replace(day=1)
            end_date = date.today()

        employees = Employee.objects.all().order_by('id')
        if dept_id:
            employees = employees.filter(department=dept_id)
        if employee_name:
            employees = employees.filter(first_name__icontains=employee_name) | employees.filter(last_name__icontains=employee_name)

        today = date.today()
        holidays = set(Holiday.objects.filter(date__range=(start_date, end_date)).values_list('date', flat=True))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employee_data.csv"'
        writer = csv.writer(response)

        # Header row
        num_days = (end_date - start_date).days + 1
        header = ["Employee Name"] + [(start_date + timedelta(days=i)).strftime("%d %b %Y") for i in range(num_days)]
        writer.writerow(header)

        for emp in employees:
            row = [f"{emp.first_name} {emp.last_name}"]
            join_date = emp.date_hired
            attendances = {att.date: att.status for att in Attendance.objects.filter(employee=emp, date__range=(start_date, end_date))}
            for i in range(num_days):
                current_date = start_date + timedelta(days=i)
                if current_date < join_date:
                    row.append('')
                elif current_date > today:
                    # Future dates show blank, except holidays
                    if current_date in holidays:
                        row.append('Holiday')
                    else:
                        row.append('')
                elif current_date in holidays:
                    row.append('Holiday')
                elif current_date.weekday() >= 5:
                    row.append('-')
                elif current_date in attendances:
                    row.append(attendances[current_date])
                else:
                    row.append('Absent')
            writer.writerow(row)

        return response