from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import Http404, JsonResponse
from .models import CustomUser, EmployeeActivityHistory
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime  # Sana tekshiruvi uchun

@method_decorator(login_required, name='dispatch')
class EmployeeListView(View):
    template_name = 'medical/employee_list.html'
    employees_per_page = 10  # Har sahifada 10 ta xodim

    def get(self, request):
        # Qidiruv so‘rovi
        search_query = request.GET.get('q', '').strip()

        # Faol xodimlarni olish
        employees = CustomUser.objects.filter(is_active_employee=True)

        # Qidiruv filtri
        if search_query:
            employees = employees.filter(
                Q(full_name__icontains=search_query) |
                Q(job_title__icontains=search_query) |
                Q(department__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )

        # Tartiblash
        employees = employees.order_by('full_name')

        # Paginatsiya
        paginator = Paginator(employees, self.employees_per_page)
        page_number = request.GET.get('page')
        try:
            employees_page = paginator.page(page_number)
        except PageNotAnInteger:
            employees_page = paginator.page(1)
        except EmptyPage:
            employees_page = paginator.page(paginator.num_pages)

        context = {
            'employees': employees_page,
            'search_query': search_query,
            'LANGUAGES': settings.LANGUAGES,
        }
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
class AddEmployeeActivityView(View):
    template_name = 'medical/add_employee_activity.html'

    def get(self, request, employee_id):
        employee = get_object_or_404(CustomUser, id=employee_id, is_active_employee=True)
        context = {
            'employee': employee,
            'LANGUAGES': settings.LANGUAGES,
        }
        return render(request, self.template_name, context)

    def post(self, request, employee_id):
        employee = get_object_or_404(CustomUser, id=employee_id, is_active_employee=True)

        activity_name = request.POST.get('activity_name', '').strip()
        activity_type = request.POST.get('activity_type', '')
        description = request.POST.get('description', '').strip()
        location_name = request.POST.get('location_name', '').strip()
        city = request.POST.get('city', '').strip()
        country = request.POST.get('country', '').strip()
        start_date = request.POST.get('start_date', '')
        end_date = request.POST.get('end_date', '') or None
        is_completed = request.POST.get('is_completed') == 'on'
        result_details = request.POST.get('result_details', '').strip()
        cost = request.POST.get('cost', '') or None
        funded_by_clinic = request.POST.get('funded_by_clinic') == 'on'
        related_operation = request.POST.get('related_operation', '').strip()
        supervisor = request.POST.get('supervisor', '').strip()
        notes = request.POST.get('notes', '').strip()

        certificate_file = request.FILES.get('certificate_file')
        additional_files = request.FILES.get('additional_files')
        expense_report = request.FILES.get('expense_report')

        if not activity_name:
            messages.error(request, "📌 Faoliyat nomi majburiy.")
            return self.get(request, employee_id)

        # Sana maydonlarini tekshirish va to'g'rilash
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None

        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        if not start_date:
            messages.warning(request, "📌 Boshlanish sanasi noto'g'ri yoki kiritilmagan, None sifatida saqlanadi.")

        activity = EmployeeActivityHistory(
            user=employee,
            activity_name=activity_name,
            activity_type=activity_type,
            description=description,
            location_name=location_name,
            city=city,
            country=country,
            start_date=start_date,
            end_date=end_date,
            is_completed=is_completed,
            result_details=result_details,
            cost=cost,
            funded_by_clinic=funded_by_clinic,
            related_operation=related_operation,
            supervisor=supervisor,
            notes=notes,
            certificate_file=certificate_file,
            additional_files=additional_files,
            expense_report=expense_report,
        )

        try:
            activity.full_clean()
            activity.save()
            messages.success(request, "✅ Faoliyat muvaffaqiyatli qo‘shildi!")
            return redirect('employee-list')
        except Exception as e:
            messages.error(request, f"📌 Xatolik yuz berdi: {str(e)}")
            return self.get(request, employee_id)
@method_decorator(login_required, name='dispatch')
class DeleteEmployeeActivityView(View):
    def delete(self, request, *args, **kwargs):
        activity_id = request.GET.get('activity_id')
        try:
            activity = EmployeeActivityHistory.objects.get(id=activity_id)
            activity.delete()
            return JsonResponse({'success': True, 'message': 'Faoliyat muvaffaqiyatli o‘chirildi!'})
        except EmployeeActivityHistory.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Faoliyat topilmadi!'}, status=404)

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            return self.delete(request, *args, **kwargs)
        return JsonResponse({'success': False, 'message': 'Faqat DELETE metod qo‘llab-quvvatlanadi!'}, status=405)