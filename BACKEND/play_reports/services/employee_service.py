import logging
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from play_reports.models import Employee
from .user_service import UserService

logger = logging.getLogger(__name__)
User = get_user_model()

class EmployeeService:
    @staticmethod
    def list_employees(user_id=None):
        """Retrieve a list of employees, optionally filtered by user_id."""
        if user_id:
            try:
                return [Employee.objects.get(user_id=user_id)]
            except Employee.DoesNotExist:
                return []
        return Employee.objects.all().select_related('user')

    @staticmethod
    def get_employee_by_id(employee_id):
        """Retrieve a single employee by their ID."""
        return get_object_or_404(Employee.objects.select_related('user'), pk=employee_id)

    @staticmethod
    def update_employee(employee_id, validated_data):
        """Update an employee's profile information."""
        employee = get_object_or_404(Employee.objects.select_related('user'), pk=employee_id)
        user = employee.user

        employee.first_name = validated_data.get('first_name', employee.first_name)
        employee.last_name = validated_data.get('last_name', employee.last_name)

        if 'email' in validated_data and validated_data['email'] != user.email:
            if User.objects.filter(email=validated_data['email']).exclude(pk=user.pk).exists():
                raise ValidationError({'email': 'An a user with that email already exists.'})
            user.email = validated_data['email']

        if 'password' in validated_data and validated_data['password']:
            user.set_password(validated_data['password'])

        user.save()
        employee.save()
        return employee

    @staticmethod
    def set_employee_activation_status(employee_id, is_active):
        """Activate or deactivate an employee's account."""
        try:
            employee = Employee.objects.select_related('user').get(pk=employee_id)
            if not employee.user:
                raise ValidationError(f'Employee with ID {employee_id} has no associated user.')
            
            UserService.set_user_activation_status(employee.user.id, is_active)
            return employee.user
        except Employee.DoesNotExist:
            raise ValidationError(f'Employee with ID {employee_id} not found.')
