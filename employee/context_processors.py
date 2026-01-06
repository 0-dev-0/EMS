def employee_context(request):
    """Add employee data to all template contexts."""
    context = {}
    if request.user.is_authenticated:
        try:
            from .models import Employee
            employee = Employee.objects.get(user=request.user)
            context['employee'] = employee
            context['employee_name'] = f"{employee.first_name} {employee.last_name}".strip()
        except Employee.DoesNotExist:
            context['employee'] = None
            context['employee_name'] = None
    return context

