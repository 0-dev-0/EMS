from datetime import date, timedelta
from .models import Attendance, Holiday
from django.contrib.auth.decorators import user_passes_test

def calculate_attendance_percentage(employee):
    start_date = employee.date_hired
    end_date = date.today()

    # Attendance records
    records = Attendance.objects.filter(
        employee=employee,
        date__range=(start_date, end_date)
    )

    record_map = {r.date: r.status for r in records}

    # Holiday dates set
    holidays = set(
        Holiday.objects.filter(
            date__range=(start_date, end_date)
        ).values_list('date', flat=True)
    )

    present = absent = leave = 0

    current = start_date
    while current <= end_date:

        # Skip weekends
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        # Skip holidays
        if current in holidays:
            current += timedelta(days=1)
            continue

        status = record_map.get(current)

        if status == 'Present':
            present += 1
        elif status == 'Leave':
            leave += 1
        else:
            absent += 1

        current += timedelta(days=1)

    total_working_days = present + absent

    if total_working_days == 0:
        return 0

    return round((present / total_working_days) * 100, 2)

def is_hr(user):
    return user.is_authenticated and user.groups.filter(name='HR').exists()

def is_employee(user):
    return user.is_authenticated and user.groups.filter(name='Employee').exists()

hr_required = user_passes_test(is_hr)
employee_required = user_passes_test(is_employee)