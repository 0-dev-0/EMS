from datetime import date

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views import View

from ..forms import (
    LoginForm,
    RegistrationForm,
    EmployeeProfileForm,
    LeaveRequestForm,
)
from ..models import Employee, Attendance, LeaveRequest
from ..utils import calculate_attendance_percentage, employee_required


def get_or_create_employee(user):

    try:
        # Try to get existing employee
        employee = Employee.objects.get(user=user)
        return employee
    except Employee.DoesNotExist:
        # Create new employee, handling potential email conflicts
        email = user.email or f"{user.username}@company.com"
        # Check if email already exists, if so, make it unique
        if Employee.objects.filter(email=email).exists():
            email = f"{user.username}@company.com"
        
        employee = Employee.objects.create(
            user=user,
            first_name=user.first_name or user.username,
            last_name=user.last_name or '',
            email=email,
            position='Employee',
            department='General',
            date_hired=date.today(),
        )
        return employee


@login_required(login_url=reverse_lazy("login"))
def landing_redirect(request):
    """Redirect authenticated users to the appropriate dashboard."""
    return redirect("dashboard")


@method_decorator(login_required(login_url=reverse_lazy("login")), name='dispatch')
@employee_required
class EmployeeDashboardView(View):


    def get(self, request):
        employee = get_or_create_employee(request.user)
        attendance_count = Attendance.objects.filter(employee=employee).count()
        leave_count = LeaveRequest.objects.filter(employee=employee).count()
        context = {
            "employee": employee,
            "total_employees": 1,
            "total_attendance": attendance_count,
            "total_leave_requests": leave_count,
        }
        return render(request, "employee/dashboard.html", context)


@method_decorator(login_required(login_url=reverse_lazy("login")), name='dispatch')
@employee_required
class MyAttendanceView(View):
    def get(self, request):
        employee = get_or_create_employee(request.user)
        attendance_days = Attendance.objects.filter(employee=employee).order_by("-date")
        attendance_percent = calculate_attendance_percentage(employee)
        return render(
            request,
            "employee/my_attendance.html",
            {
                "attendance_days": attendance_days,
                "attendance_percent": attendance_percent,
            },
        )


@method_decorator(login_required(login_url=reverse_lazy("login")), name='dispatch')
@employee_required
class MyLeaveRequestsView(View):
    def get(self, request):
        employee = get_or_create_employee(request.user)
        leave_requests = LeaveRequest.objects.filter(employee=employee).order_by(
            "-start_date"
        )
        return render(
            request,
            "employee/my_leave_requests.html",
            {"leave_requests": leave_requests},
        )


@method_decorator(login_required(login_url=reverse_lazy("login")), name='dispatch')
@employee_required
class ApplyLeaveView(View):
    def get(self, request):
        form = LeaveRequestForm()
        return render(request, "employee/apply_leave.html", {"form": form})

    def post(self, request):
        employee = get_or_create_employee(request.user)
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = employee
            leave.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect("my_leave_requests")
        return render(request, "employee/apply_leave.html", {"form": form})


@method_decorator(login_required(login_url=reverse_lazy("login")), name='dispatch')
@employee_required
class MyProfileView(View):
    def get(self, request):
        employee = get_or_create_employee(request.user)
        return render(request, "employee/my_profile.html", {"employee": employee})


@method_decorator(login_required(login_url=reverse_lazy("login")), name='dispatch')
@employee_required
class EditMyProfileView(View):
    def get(self, request):
        employee = get_or_create_employee(request.user)
        form = EmployeeProfileForm(instance=employee)
        return render(
            request,
            "employee/edit_profile.html",
            {"employee": employee, "form": form},
        )

    def post(self, request):
        employee = get_or_create_employee(request.user)
        form = EmployeeProfileForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            # Sync User model with Employee data
            user = request.user
            user.first_name = employee.first_name
            user.last_name = employee.last_name
            user.email = employee.email
            user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("my_profile")
        return render(
            request,
            "employee/edit_profile.html",
            {"employee": employee, "form": form},
        )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        
        form = LoginForm(request=request)
        return render(request, "registration/login.html", {"form": form})

    @method_decorator(csrf_protect)
    def post(self, request):
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # All users go to the same dashboard
            next_url = request.GET.get('next', None)
            if next_url:
                return redirect(next_url)
            return redirect("dashboard")
        return render(request, "registration/login.html", {"form": form})


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = RegistrationForm()
        return render(request, "registration/register.html", {"form": form})

    @method_decorator(csrf_protect)
    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            # Create basic employee record
            from datetime import date
            Employee.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                position=request.POST.get("position", "Employee"),
                department=request.POST.get("department", "General"),
                date_hired=request.POST.get("date_hired") or date.today(),
            )
            # Add user to Employee group
            from django.contrib.auth.models import Group
            employee_group, _ = Group.objects.get_or_create(name="Employee")
            user.groups.add(employee_group)
            messages.success(request, "Account created successfully. Please log in.")
            return redirect("login")
        return render(request, "registration/register.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")