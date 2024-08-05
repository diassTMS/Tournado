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
from .models import Order, OrderItem, CURRENCY
from .forms import OrderCreateForm, OrderEditForm
from .tables import ProductTable, OrderItemTable, OrderTable, AdminOrderTable
from tournaments.models import Tournament, Entry
from Tournado import renderers
import datetime
from django.contrib.auth.models import User

class OrderListView(TemplateView):
    model = User
    template_name = 'orders/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.pop('pk')
        user = User.objects.get(id=pk) 
        qs = Order.objects.filter(user=user)
        print(self.request.user.groups.first())
        if self.request.user.groups.first().name == "Admin":
            context['orders'] = AdminOrderTable(qs)
        else:
            context['orders'] = OrderTable(qs)
        context['userInput'] = user
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
def paid_order(request, pk):
    print('hi')
    instance = get_object_or_404(Order, id=pk)
    user = instance.user
    
    if instance.paid == False:
        instance.paid = True
    else:
        instance.paid = False
    instance.save()
    print('save')
    data = dict()
    instance.refresh_from_db()
    order_list = Order.objects.filter(user=instance.user)
    if request.user.groups.first().name == "Admin":
        orders = AdminOrderTable(order_list)
    else:
        orders = OrderTable(order_list)
    RequestConfig(request).configure(orders)
    data['result'] = render_to_string(template_name='orders/include/order_table.html',
                                      request=request,
                                      context={
                                          'userInput': instance.user,
                                          'orders': orders
                                      }
                                      )
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