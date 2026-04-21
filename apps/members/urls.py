from django.urls import path
from .views import (
    AddEmployeeActivityView,
    DeleteEmployeeActivityView,
    EditEmployeeActivityView,
    EmployeeActivityDetailView,
    EmployeeListView,
)

urlpatterns = [
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:employee_id>/add-activity/', AddEmployeeActivityView.as_view(), name='add-employee-activity'),
    path(
        'employees/<int:employee_id>/activities/<int:activity_id>/',
        EmployeeActivityDetailView.as_view(),
        name='employee-activity-detail',
    ),
    path(
        'employees/<int:employee_id>/activities/<int:activity_id>/edit/',
        EditEmployeeActivityView.as_view(),
        name='edit-employee-activity',
    ),
    path('employees/activity/delete/', DeleteEmployeeActivityView.as_view(), name='delete-employee-activity'),
]
