from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from play_reports.models import Employee
from play_reports.serializers.employee_serializers import (
    EmployeeSerializer,
    EmployeeDetailSerializer,
    EmployeeUpdateSerializer
)

User = get_user_model()

class EmployeeListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                employee = Employee.objects.get(user_id=user_id)
                serializer = EmployeeDetailSerializer(employee)
                return Response([serializer.data])  # Retourne un tableau pour maintenir la cohérence
            except Employee.DoesNotExist:
                return Response([], status=status.HTTP_404_NOT_FOUND)
        
        # Si pas de user_id, retourner tous les employés
        queryset = Employee.objects.all().select_related('user')
        serializer = EmployeeSerializer(queryset, many=True)
        return Response(serializer.data)

class EmployeeDetailController(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, pk):
        try:
            return Employee.objects.select_related('user').get(pk=pk)
        except Employee.DoesNotExist:
            return None

    def get(self, request, pk):
        employee = self.get_object(pk)
        if not employee:
            return Response(
                {'error': 'Employé non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = EmployeeDetailSerializer(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        employee = self.get_object(pk)
        if not employee:
            return Response(
                {'error': 'Employé non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = EmployeeUpdateSerializer(
            employee,
            data=request.data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            updated_employee = serializer.save()
            return Response(
                EmployeeDetailSerializer(updated_employee).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EmployeeUpdateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, pk):
        try:
            return Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return None

    def put(self, request, pk):
        employee = self.get_object(pk)
        if not employee:
            return Response(
                {'error': 'Employé non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployeeUpdateSerializer(
            employee,
            data=request.data,
            context={'request': request},
            partial=True
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_employee = serializer.save()
            return Response(EmployeeDetailSerializer(updated_employee).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EmployeeDeactivateController(APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, pk):
        employee = get_object_or_404(Employee.objects.select_related('user'), pk=pk)
        employee.user.is_active = False
        employee.user.save()
        return Response({'message': 'Employé désactivé.'}, status=status.HTTP_200_OK)

class EmployeeActivateController(APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, pk):
        try:
            employee = Employee.objects.select_related('user').get(pk=pk)
            employee.user.is_active = True
            employee.user.save()
            return Response(
                {'message': 'Employé activé avec succès.'}, 
                status=status.HTTP_200_OK
            )
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employé introuvable.'}, 
                status=status.HTTP_404_NOT_FOUND
            )