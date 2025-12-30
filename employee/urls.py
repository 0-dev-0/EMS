from django.urls import path
from .views import (
    CreateLeaveRequestView, home, DashboardView,
    EmployeeListView, EmployeeDetailView, AttendanceSummaryView,
    AttendanceDetailView, DeleteAttendanceView, UpdateAttendanceView,
    LeaveRequestListView, LeaveRequestDetailView,
    create_employee, update_employee, delete_employee
)

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/create/', create_employee.as_view(), name='create_employee'),
    path('employees/update/<int:pk>/', update_employee.as_view(), name='update_employee'),
    path('employees/delete/<int:pk>/', delete_employee.as_view(), name='delete_employee'),

    path('attendance/', AttendanceSummaryView.as_view(), name='attendance_summary'),

    path('attendance/<int:employee_id>/', AttendanceDetailView.as_view(), name='attendance_detail'),
    
    path('attendance/delete/<int:pk>/', DeleteAttendanceView.as_view(), name='delete_attendance'),

    path('attendance/update/<int:employee_id>/<str:date>/', UpdateAttendanceView.as_view(), name='update_attendance'),

    path('leave/create/', CreateLeaveRequestView.as_view(), name='create_leave_request'),
    
    path('leave/', LeaveRequestListView.as_view(), name='leave_request_list'),
    
    path('leave/<int:pk>/', LeaveRequestDetailView.as_view(), name='leave_request_detail'),
    
]
