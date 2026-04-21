from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View

from .models import CustomUser, EmployeeActivityHistory


class EmployeeActivityFormMixin:
    template_name = "medical/add_employee_activity.html"

    def get_activity_type_choices(self):
        return EmployeeActivityHistory._meta.get_field("activity_type").choices

    def get_form_context(self, employee, activity=None):
        return {
            "employee": employee,
            "activity": activity,
            "activity_type_choices": self.get_activity_type_choices(),
            "LANGUAGES": settings.LANGUAGES,
        }

    @staticmethod
    def parse_date(date_str):
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def build_activity_data(self, request):
        return {
            "activity_name": request.POST.get("activity_name", "").strip(),
            "activity_type": request.POST.get("activity_type", "training"),
            "description": request.POST.get("description", "").strip(),
            "location_name": request.POST.get("location_name", "").strip(),
            "city": request.POST.get("city", "").strip(),
            "country": request.POST.get("country", "").strip(),
            "start_date": self.parse_date(request.POST.get("start_date", "")),
            "end_date": self.parse_date(request.POST.get("end_date", "") or None),
            "is_completed": request.POST.get("is_completed") == "on",
            "result_details": request.POST.get("result_details", "").strip(),
            "cost": request.POST.get("cost", "") or None,
            "funded_by_clinic": request.POST.get("funded_by_clinic") == "on",
            "related_operation": request.POST.get("related_operation", "").strip(),
            "supervisor": request.POST.get("supervisor", "").strip(),
            "notes": request.POST.get("notes", "").strip(),
        }

    def apply_uploaded_files(self, request, activity):
        for field_name in ("certificate_file", "additional_files", "expense_report"):
            uploaded_file = request.FILES.get(field_name)
            if uploaded_file:
                setattr(activity, field_name, uploaded_file)


@method_decorator(login_required, name="dispatch")
class EmployeeListView(View):
    template_name = "medical/employee_list.html"
    employees_per_page = 10

    def get(self, request):
        search_query = request.GET.get("q", "").strip()
        employees = CustomUser.objects.filter(is_active_employee=True).prefetch_related("activity_history")

        if search_query:
            employees = employees.filter(
                Q(full_name__icontains=search_query)
                | Q(job_title__icontains=search_query)
                | Q(department__icontains=search_query)
                | Q(employee_id__icontains=search_query)
            )

        employees = employees.order_by("full_name")
        paginator = Paginator(employees, self.employees_per_page)
        page_number = request.GET.get("page")

        try:
            employees_page = paginator.page(page_number)
        except PageNotAnInteger:
            employees_page = paginator.page(1)
        except EmptyPage:
            employees_page = paginator.page(paginator.num_pages)

        context = {
            "employees": employees_page,
            "search_query": search_query,
            "total_employees": CustomUser.objects.filter(is_active_employee=True).count(),
            "total_activities": EmployeeActivityHistory.objects.count(),
            "completed_activities": EmployeeActivityHistory.objects.filter(is_completed=True).count(),
            "open_activities": EmployeeActivityHistory.objects.filter(is_completed=False).count(),
            "LANGUAGES": settings.LANGUAGES,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
class AddEmployeeActivityView(EmployeeActivityFormMixin, View):
    def get(self, request, employee_id):
        employee = get_object_or_404(CustomUser, id=employee_id, is_active_employee=True)
        return render(request, self.template_name, self.get_form_context(employee))

    def post(self, request, employee_id):
        employee = get_object_or_404(CustomUser, id=employee_id, is_active_employee=True)
        activity_data = self.build_activity_data(request)

        if not activity_data["activity_name"]:
            messages.error(request, "Faoliyat nomi majburiy.")
            return self.get(request, employee_id)

        activity = EmployeeActivityHistory(user=employee, **activity_data)
        self.apply_uploaded_files(request, activity)

        try:
            activity.full_clean()
            activity.save()
            messages.success(request, "Faoliyat muvaffaqiyatli qo'shildi.")
            return redirect("employee-list")
        except Exception as exc:
            messages.error(request, f"Xatolik yuz berdi: {exc}")
            return self.get(request, employee_id)


@method_decorator(login_required, name="dispatch")
class EmployeeActivityDetailView(View):
    template_name = "medical/employee_activity_detail.html"

    def get(self, request, employee_id, activity_id):
        employee = get_object_or_404(CustomUser, id=employee_id, is_active_employee=True)
        activity = get_object_or_404(EmployeeActivityHistory, id=activity_id, user=employee)
        return render(request, self.template_name, {
            "employee": employee,
            "activity": activity,
        })


@method_decorator(login_required, name="dispatch")
class EditEmployeeActivityView(EmployeeActivityFormMixin, View):
    def get(self, request, employee_id, activity_id):
        employee = get_object_or_404(CustomUser, id=employee_id, is_active_employee=True)
        activity = get_object_or_404(EmployeeActivityHistory, id=activity_id, user=employee)
        return render(request, self.template_name, self.get_form_context(employee, activity))

    def post(self, request, employee_id, activity_id):
        employee = get_object_or_404(CustomUser, id=employee_id, is_active_employee=True)
        activity = get_object_or_404(EmployeeActivityHistory, id=activity_id, user=employee)
        activity_data = self.build_activity_data(request)

        if not activity_data["activity_name"]:
            messages.error(request, "Faoliyat nomi majburiy.")
            return self.get(request, employee_id, activity_id)

        for field_name, value in activity_data.items():
            setattr(activity, field_name, value)
        self.apply_uploaded_files(request, activity)

        try:
            activity.full_clean()
            activity.save()
            messages.success(request, "Faoliyat muvaffaqiyatli yangilandi.")
            return redirect("employee-activity-detail", employee_id=employee.id, activity_id=activity.id)
        except Exception as exc:
            messages.error(request, f"Xatolik yuz berdi: {exc}")
            return self.get(request, employee_id, activity_id)


@method_decorator(login_required, name="dispatch")
class DeleteEmployeeActivityView(View):
    def post(self, request, *args, **kwargs):
        activity_id = request.POST.get("activity_id")
        next_url = request.POST.get("next") or "employee-list"
        activity = get_object_or_404(EmployeeActivityHistory, id=activity_id)
        activity.delete()
        messages.success(request, "Faoliyat muvaffaqiyatli o'chirildi.")
        return redirect(next_url)

    def delete(self, request, *args, **kwargs):
        activity_id = request.GET.get("activity_id")
        try:
            activity = EmployeeActivityHistory.objects.get(id=activity_id)
            activity.delete()
            return JsonResponse({"success": True, "message": "Faoliyat muvaffaqiyatli o'chirildi!"})
        except EmployeeActivityHistory.DoesNotExist:
            return JsonResponse({"success": False, "message": "Faoliyat topilmadi!"}, status=404)

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            return self.post(request, *args, **kwargs)
        if request.method == "DELETE":
            return self.delete(request, *args, **kwargs)
        return JsonResponse({"success": False, "message": "Faqat POST yoki DELETE metod qo'llab-quvvatlanadi!"}, status=405)
