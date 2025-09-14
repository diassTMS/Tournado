from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.query import QuerySet
from django.views.generic import UpdateView, ListView, TemplateView
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Sum
from django.urls import reverse, reverse_lazy
from django_tables2 import RequestConfig
from django.db.models import F, Q
from .models import Order, OrderItem, CURRENCY
from .forms import OrderCreateForm, OrderEditForm
from .tables import ProductTable, OrderItemTable, OrderTable, AdminOrderTable
from tournaments.models import Tournament, Entry
from Tournado import renderers
import datetime
from django.contrib.auth.models import User
from users.models import Profile
from datetime import date, datetime
import csv
from django.http import HttpResponse
from django.db import connection

class UserEntryListView(TemplateView):
    model = User
    template_name = 'orders/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.pop('pk')
        user = User.objects.get(id=pk)

        season = self.request.GET.get("season")
        today = date.today()

        if not season:
            # Default to current season
            if today.month >= 9:  # September or later
                season_start = date(today.year, 9, 1)
                season_end = date(today.year + 1, 8, 31)
                season_label = f"{today.year}-{str(today.year + 1)[-2:]}"
            else:
                season_start = date(today.year - 1, 9, 1)
                season_end = date(today.year, 8, 31)
                season_label = f"{today.year - 1}-{str(today.year)[-2:]}"
        else:
            try:
                start_year, end_year = map(int, season.split("-"))
                season_start = date(start_year, 9, 1)
                season_end = date(end_year if end_year > 100 else 2000 + end_year, 8, 31)
                season_label = season
            except ValueError:
                # fallback to current season
                if today.month >= 9:
                    season_start = date(today.year, 9, 1)
                    season_end = date(today.year + 1, 8, 31)
                    season_label = f"{today.year}-{str(today.year + 1)[-2:]}"
                else:
                    season_start = date(today.year - 1, 9, 1)
                    season_end = date(today.year, 8, 31)
                    season_label = f"{today.year - 1}-{str(today.year)[-2:]}"

        # Filter entries
        if user.groups.first().name == "Admin":
            # Admins see all entries for the season or all entries
            qs = Entry.objects.filter(Q(invoiced=False) & Q(tournament__date__range=[season_start, season_end])
            ).order_by(F('tournament__date').desc(), F('tournament__name'))
            
            owing = (Entry.objects.filter(tournament__date__range=[season_start, season_end], invoiced=False).aggregate(total=Sum(F('tournament__entryPrice'))))['total'] or 0            
            invoiced = (Entry.objects.filter(tournament__date__range=[season_start, season_end], invoiced=True).aggregate(total=Sum(F('tournament__entryPrice'))))['total'] or 0            
            total = owing + invoiced

        else:
            # Non-admins see only their own entries
            qs = Entry.objects.filter(Q(user=user) & Q(tournament__date__range=[season_start, season_end])
            ).order_by(F('tournament__date').desc(), F('tournament__name'))

            owing = (Entry.objects.filter(user=user, tournament__date__range=[season_start, season_end], invoiced=False).aggregate(total=Sum(F('tournament__entryPrice'))))['total'] or 0            
            invoiced = (Entry.objects.filter(user=user, tournament__date__range=[season_start, season_end], invoiced=True).aggregate(total=Sum(F('tournament__entryPrice'))))['total'] or 0            
            total = owing + invoiced
        
        # Choose table type
        if self.request.user.groups.first().name == "Admin":
            table = AdminOrderTable(qs)
        else:
            table = OrderTable(qs)

        # Apply pagination (25 rows per page for example)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(table)
        context['orders'] = table

        # Gather all available seasons starting from 2024-25
        seasons = []
        for t in Tournament.objects.dates("date", "year"):
            start_year = t.year if t.month >= 9 else t.year - 1
            if start_year < 2024:
                continue
            end_year_short = str(start_year + 1)[-2:]
            label = f"{start_year}-{end_year_short}"
            if label not in seasons:
                seasons.append(label)
        seasons = sorted(seasons, reverse=True)

        # Update context
        context.update({
            'userInput': user,
            'owing': owing,
            'invoiced': invoiced,
            'total': total,
            'entries': qs.count(),
            'season': season_label,
            'seasons': seasons,
        })

        return context
    
@login_required
def auto_create_order_view(request, pk):
    userId = pk
    user = User.objects.get(pk=userId)
    print(user)
    new_order = Order.objects.create(
        title='Order 69',
        user=user,
        date=datetime.datetime.today().date()

    )
    new_order.title = f'Order #{new_order.id}'
    new_order.save()
    return redirect(new_order.get_edit_url())

class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    template_name = 'orders/order_update.html'
    form_class = OrderEditForm

    def get_success_url(self):
        return reverse('update_order', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = self.object
        user = instance.user
        print(user)
        context['userInput'] = user
        group = user.groups.first()
        if group.name == "Admin":
            qs_p = Tournament.objects.all()
        else:
            qs_p = Tournament.objects.filter(date__gte=datetime.datetime.today().date(), group=group)
        products = ProductTable(qs_p)
        order_items = OrderItemTable(instance.order_items.all())
        RequestConfig(self.request).configure(products)
        RequestConfig(self.request).configure(order_items)
        context.update(locals())
        return context
    
@login_required
def ajax_add_product(request, pk, dk):
    instance = get_object_or_404(Order, id=pk)
    tournament = get_object_or_404(Tournament, id=dk)
    order_item, created = OrderItem.objects.get_or_create(order=instance, tournament=tournament)
    
    if created:
        order_item.tournament = tournament
        order_item.qty = 1
        order_item.price = tournament.entryPrice
        entry = Entry(tournament = tournament,
                        user = instance.user,
                        teamName = f'{instance.user.username}',
                        )
        entry.save()
        print('entry')
    else:
        order_item.qty += 1
        entry = Entry(tournament = tournament,
                        user = instance.user,
                        teamName = f'{instance.user.username} {(order_item.qty - 1)}',
                        )
        entry.save()
        print('entry')

    order_item.save()
    print('save')
    instance.refresh_from_db()
    order_items = OrderItemTable(instance.order_items.all())
    RequestConfig(request).configure(order_items)
    data = dict()
    data['result'] = render_to_string(template_name='orders/include/order_container.html',
                                      request=request,
                                      context={'instance': instance,
                                               'order_items': order_items
                                               }
                                    )
    return JsonResponse(data)

@login_required
def ajax_modify_order_item(request, pk):
    order_item = get_object_or_404(OrderItem, id=pk)
    instance = order_item.order

    entry = Entry.objects.filter(user=instance.user, tournament=order_item.tournament).order_by('-pk').first()
    print('del', entry)
    entry.delete()
    
    order_item.qty -= 1
    order_item.save()
    if order_item.qty == 0:
        order_item.delete()

    data = dict()
    instance.refresh_from_db()
    print(instance.final_value)
    order_items = OrderItemTable(instance.order_items.all())
    RequestConfig(request).configure(order_items)
    data['result'] = render_to_string(template_name='orders/include/order_container.html',
                                      request=request,
                                      context={
                                          'instance': instance,
                                          'order_items': order_items
                                      }
                                      )
    return JsonResponse(data)

@login_required
def submit_order(request, pk):
    instance = get_object_or_404(Order, id=pk)
    user = instance.user
    if len(instance.order_items.all()) == 0:
        instance.delete()
    else:
        instance.save()
        messages.success(request, 'Order saved!')

    return redirect(reverse_lazy('order-list',  kwargs={'pk': user.id}))

@login_required
def delete_order(request, pk):
    instance = get_object_or_404(Order, id=pk)
    user = instance.user
    order_items = instance.order_items.all()
    for tourn in order_items:
        for i in range(tourn.qty):
            try:
                entry = Entry.objects.filter(user=user, tournament=tourn.tournament).order_by('-pk').first()
                print('del', entry)
                entry.delete()
            except:
                print('no entries')

    instance.delete()
    messages.warning(request, 'Order deleted!')

    data = dict()
    order_list = Order.objects.filter(user=user)
    if request.user.groups.first().name == "Admin":
        orders = AdminOrderTable(order_list)
    else:
        orders = OrderTable(order_list)
    RequestConfig(request).configure(orders)
    data['result'] = render_to_string(template_name='orders/include/order_table.html',
                                      request=request,
                                      context={
                                          'userInput': user,
                                          'orders': orders
                                      }
                                      )
    return JsonResponse(data)

@login_required
def invoice_tourn(request, pk): 
    instance = get_object_or_404(Entry, id=pk)
    user = instance.user
    userInput = request.GET.get('userInput')

    # Toggle invoice
    instance.invoiced = not instance.invoiced
    instance.save()

    # Get season param
    season = request.GET.get('season')
    today = date.today()

    if not season:
        # Default to current season
        if today.month >= 9:  # September or later
            season_start = date(today.year, 9, 1)
            season_end = date(today.year + 1, 8, 31)
            season_label = f"{today.year}-{str(today.year + 1)[-2:]}"
        else:
            season_start = date(today.year - 1, 9, 1)
            season_end = date(today.year, 8, 31)
            season_label = f"{today.year - 1}-{str(today.year)[-2:]}"
    else:
        try:
            start_year, end_year = map(int, season.split("-"))
            season_start = date(start_year, 9, 1)
            season_end = date(end_year if end_year > 100 else 2000 + end_year, 8, 31)
            season_label = season
        except ValueError:
            # fallback to current season
            if today.month >= 9:
                season_start = date(today.year, 9, 1)
                season_end = date(today.year + 1, 8, 31)
                season_label = f"{today.year}-{str(today.year + 1)[-2:]}"
            else:
                season_start = date(today.year - 1, 9, 1)
                season_end = date(today.year, 8, 31)
                season_label = f"{today.year - 1}-{str(today.year)[-2:]}"

    # Filter entries
    if userInput == "Admin":
        # Admins see all entries for the season or all entries
        qs = Entry.objects.filter(Q(invoiced=False) & Q(tournament__date__range=[season_start, season_end])
        ).order_by(F('tournament__date').desc(), F('tournament__name'))
        
        owing = (Entry.objects.filter(tournament__date__range=[season_start, season_end], invoiced=False).aggregate(total=Sum(F('tournament__entryPrice'))))['total'] or 0            
        invoiced = (Entry.objects.filter(tournament__date__range=[season_start, season_end], invoiced=True).aggregate(total=Sum(F('tournament__entryPrice'))))['total'] or 0            

    else:
        # Non-admins see only their own entries
        qs = Entry.objects.filter(Q(user=user) & Q(tournament__date__range=[season_start, season_end])
        ).order_by(F('tournament__date').desc(), F('tournament__name'))

        owing = (Entry.objects.filter(user=user, tournament__date__range=[season_start, season_end], invoiced=False).aggregate(total=Sum(F('tournament__entryPrice'))))['total'] or 0            
        invoiced = (Entry.objects.filter(user=user, tournament__date__range=[season_start, season_end], invoiced=True).aggregate(total=Sum(F('tournament__entryPrice'))))['total'] or 0            
    
    total = owing + invoiced
        
    # Seasons dropdown
    seasons = []
    for t in Tournament.objects.dates("date", "year"):
        start_year = t.year if t.month >= 9 else t.year - 1
        if start_year < 2024:
            continue
        end_year_short = str(start_year + 1)[-2:]
        label = f"{start_year}-{end_year_short}"
        if label not in seasons:
            seasons.append(label)
    seasons = sorted(seasons, reverse=True)

    # Choose table type
    if request.user.groups.first().name == "Admin":
        table = AdminOrderTable(qs)
    else:
        table = OrderTable(qs)

    # Apply pagination (25 rows per page for example)
    RequestConfig(request, paginate={'per_page': 25}).configure(table)

    data = {
        'table': render_to_string(
            template_name='orders/include/order_table.html',
            request=request,
            context={'userInput': userInput, 'orders': table},
        ),
        'entries': qs.count(),
        'owing': owing,
        'invoiced': invoiced,
        'total': total,
        'season': season_label,
        'seasons': seasons,
    }
    return JsonResponse(data)
   
def InvoicePdf(request, pk):
    order = get_object_or_404(Order, id=pk)
    order_items = order.order_items.all()
    invoice = []

    for i in range(len(order_items)):
        row = []
        row.append(order_items[i].tournament)
        row.append(order_items[i].qty)
        row.append(order_items[i].price)
        row.append(f'20%')
        row.append(order_items[i].total_price)
        invoice.append(row)
    
    date = datetime.datetime.today().date()

    data = {
        'invoice': invoice,
        'date': date,
    }
    
    return renderers.render_to_pdf('invoices/hockey-fever-template.html', data)

@login_required
def admin_csv_download(request):
    pk = request.GET.get('user_id')  # The user whose page we’re viewing
    user = User.objects.get(id=pk)

    # Only allow if this user is an admin
    if user.groups.first().name != "Admin":
        return HttpResponse("Unauthorized", status=403)

    start = request.GET.get('start')
    end = request.GET.get('end')
    invNum = request.GET.get('invNum', 1)

    if not start or not end:
        return HttpResponse("Start and end dates required", status=400)

    # Convert to proper date format
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")
        invNum = int(invNum)

    except ValueError:
        return HttpResponse("Invalid date format", status=400)

    vendor = connection.vendor  # "sqlite", "mysql", "postgresql", etc.

    if vendor == "sqlite":
        query = """
            SELECT 
                auth_user.username AS "*ContactName", 
                users_profile.invoice_email AS "*EmailAddress",
                DATE('now') AS "*InvoiceDate",
                DATE('now','+7 day') AS "*DueDate",
                'GHA Tournaments' AS "*Reference", 
                tournaments_tournament.name || ' - ' || tournaments_tournament.date AS "*Description",
                COUNT(*) AS "*Quantity",
                tournaments_tournament.entryPrice AS "*UnitAmount",
                'GBP' AS "*Currency",
                '20%% (VAT on Income)' AS "*TaxType"
            FROM auth_user
            JOIN users_profile ON auth_user.id = users_profile.user_id
            JOIN tournaments_entry ON tournaments_entry.user_id = auth_user.id
            JOIN tournaments_tournament ON tournaments_entry.tournament_id = tournaments_tournament.id
            WHERE auth_user.username != 'Hockey_Fever'
            AND tournaments_tournament.date BETWEEN :start AND :end
            GROUP BY auth_user.username, tournaments_tournament.name, tournaments_tournament.date;
        """
        params = {"start": start_date, "end": end_date}

    elif vendor == "mysql":
        query = """
            SELECT 
                auth_user.username AS "*ContactName", 
                users_profile.invoice_email AS "*EmailAddress",
                CURDATE() AS "*InvoiceDate",
                DATE_ADD(CURDATE(), INTERVAL 7 DAY) AS "*DueDate",
                'GHA Tournaments' AS "*Reference", 
                CONCAT(tournaments_tournament.name, ' - ', tournaments_tournament.date) AS "*Description",
                COUNT(*) AS "*Quantity",
                tournaments_tournament.entryPrice AS "*UnitAmount",
                'GBP' AS "*Currency",
                '20%% (VAT on Income)' AS "*TaxType"
            FROM auth_user
            JOIN users_profile ON auth_user.id = users_profile.user_id
            JOIN tournaments_entry ON tournaments_entry.user_id = auth_user.id
            JOIN tournaments_tournament ON tournaments_entry.tournament_id = tournaments_tournament.id
            WHERE auth_user.username != 'Hockey_Fever'
            AND tournaments_tournament.date BETWEEN %s AND %s
            GROUP BY auth_user.username, tournaments_tournament.name, tournaments_tournament.date;
        """
        params = [start_date, end_date]

    else:
        return HttpResponse(f"Database vendor {vendor} not supported", status=500)
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)        
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

    # Add invoice number column
    columns.append("*InvoiceNumber")

    # Generate invoice numbers
    invoice_map = {}
    counter = invNum
    updated_rows = []

    for row in rows:
        username = row[0]  # username is first column
        if username not in invoice_map:
            invoice_map[username] = f"GHA-{counter:04d}"
            counter += 1
        invoice_number = invoice_map[username]
        updated_rows.append(row + (invoice_number,))  # append at end

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="entries_{start}_{end}.csv"'

    writer = csv.writer(response)
    writer.writerow(columns)
    for row in updated_rows:
        writer.writerow(row)

    return response

@login_required
def admin_bulk_invoice(request):
    if request.method != "POST":
        return JsonResponse({"message": "Invalid request"}, status=400)

    pk = request.POST.get('user_id')
    user = User.objects.get(id=pk)

    # Only allow if this user is admin
    if user.groups.first().name != "Admin":
        return JsonResponse({"message": "Unauthorized"}, status=403)

    start = request.POST.get('start_date')
    end = request.POST.get('end_date')

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"message": "Invalid date format"}, status=400)

    # Update all entries in the date range
    entries = Entry.objects.filter(tournament__date__range=[start_date, end_date], invoiced=False)
    count = entries.update(invoiced=True)

    return JsonResponse({"message": f"{count} entries marked as invoiced"})

