import csv
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from .views.employee_views import home
from .models import Employee, Attendance
from .utils import hr_required

from .views.employee_views import (
    EmployeeDashboardView,
    MyAttendanceView,
    MyLeaveRequestsView,
    ApplyLeaveView,
    MyProfileView,
    EditMyProfileView,
    LoginView,
    RegisterView,
    logout_view,
)
from .views.hr_views import (

    HRDashboardView,
    EmployeeListView,
    EmployeeDetailView,
    CreateEmployeeView,
    UpdateEmployeeView,
    DeleteEmployeeView,
    LeaveApprovalView,
    LeaveRequestListView,
    LeaveRequestDetailView,
    AttendanceSummaryView,
    AttendanceDetailView,
    DeleteAttendanceView,
    UpdateAttendanceView,
    DeleteLeaveRequestView,
)

@ensure_csrf_cookie
def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "registration/login.html")

