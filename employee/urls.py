from django.urls import path
from .views.employee_views import (
    EmployeeDashboardView,
    MyAttendanceView,
    MyLeaveRequestsView,
    MyProfileView,
    EditMyProfileView,
    ApplyLeaveView,
    LoginView,
    RegisterView,
    logout_view,
)
from .views.hr_views import (
    ExportDataCSVView,
    ExportDataPageView,
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

urlpatterns = [
    path("", LoginView.as_view(), name="home"),
    path("login/", LoginView.as_view(), name="login"),

    path("dashboard/", EmployeeDashboardView.as_view(), name="dashboard"),

    # Auth

    path("logout/", logout_view, name="logout"),
    path("register/", RegisterView.as_view(), name="register"),

    # Employee self-service views
    path("my-attendance/", MyAttendanceView.as_view(), name="my_attendance"),
    path("my-leave-requests/", MyLeaveRequestsView.as_view(), name="my_leave_requests"),
    path("my-profile/", MyProfileView.as_view(), name="my_profile"),
    path("my-profile/edit/", EditMyProfileView.as_view(), name="edit_my_profile"),
    path("apply-leave/", ApplyLeaveView.as_view(), name="apply_leave"),

    # HR views
    path("hr/dashboard/", HRDashboardView.as_view(), name="hr_dashboard"),

    path("hr/employees/", EmployeeListView.as_view(), name="employee_list"),
    path("hr/employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee_detail"),
    path("hr/employees/create/", CreateEmployeeView.as_view(), name="create_employee"),
    path("hr/employees/update/<int:pk>/", UpdateEmployeeView.as_view(), name="update_employee"),
    path("hr/employees/delete/<int:pk>/", DeleteEmployeeView.as_view(), name="delete_employee"),

    path("hr/attendance/", AttendanceSummaryView.as_view(), name="attendance_summary"),
    path("hr/attendance/<int:employee_id>/", AttendanceDetailView.as_view(), name="attendance_detail"),
    path("hr/attendance/delete/<int:pk>/", DeleteAttendanceView.as_view(), name="delete_attendance"),
    path(
        "hr/attendance/update/<int:employee_id>/<str:date>/",
        UpdateAttendanceView.as_view(),
        name="update_attendance",
    ),

    path("hr/leave/", LeaveRequestListView.as_view(), name="leave_request_list"),
    path("hr/leave/<int:pk>/", LeaveRequestDetailView.as_view(), name="leave_request_detail"),
    path("hr/leave/delete/<int:pk>/", DeleteLeaveRequestView.as_view(), name="delete_leave_request"),
    path("hr/leave-approvals/", LeaveApprovalView.as_view(), name="leave_approvals"),
    path("hr/leave-approvals/<int:pk>/", LeaveApprovalView.as_view(), name="leave_approval_action"),
    path('hr/export-data/', ExportDataPageView.as_view(), name='export_data_page'),

    path('hr/export-data/csv/', ExportDataCSVView.as_view(), name='export_data'),
]
