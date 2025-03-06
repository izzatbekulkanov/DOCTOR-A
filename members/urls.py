from django.urls import path
from .views import EmployeeListView, AddEmployeeActivityView, DeleteEmployeeActivityView

urlpatterns = [
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:employee_id>/add-activity/', AddEmployeeActivityView.as_view(), name='add-employee-activity'),
    path('employees/activity/delete/', DeleteEmployeeActivityView.as_view(), name='delete-employee-activity'),
]
