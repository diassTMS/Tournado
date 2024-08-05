import django_tables2 as tables
from .models import OrderItem, Order
from tournaments.models import Tournament
from django.utils.safestring import mark_safe
from django_tables2.utils import Accessor, AttributeDict, computed_values
from django.urls import reverse, reverse_lazy


class OrderTable(tables.Table):
    tag_final_value = tables.Column(orderable=False, verbose_name='Value')
    paid = tables.BooleanColumn(orderable=False, verbose_name='Paid', attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    action = tables.TemplateColumn(
        '<a href="{{ record.get_edit_url }}" class="btn btn-info"><i class="fa fa-edit"></i></a>', orderable=False, verbose_name="Edit", attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })

    class Meta:
        model = Order
        template_name = 'django_tables2/bootstrap.html'
        fields = ['date', 'title', 'tag_final_value',]

    def render_paid(self, value, bound_column, record):
        if value:
            return mark_safe(f'''<i style="color: green; font-size: 26px;" class="fa-solid fa-check"></i>''')
        else:
            return mark_safe(f'''<i style="color: red; font-size: 24px;" class="fa-solid fa-x"></i>''')

class AdminOrderTable(tables.Table):
    tag_final_value = tables.Column(orderable=False, verbose_name='Value')
    action = tables.TemplateColumn(
        '<a href="{{ record.get_edit_url }}" class="btn btn-info"><i class="fa fa-edit"></i></a>', orderable=False, attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    delete = tables.TemplateColumn('''
            <a onclick="return confirm('Are you sure?')" class="delete_button" data-href="{% url 'delete-order' record.id %}" style="color: #AF291D;"><i class="fa-solid fa-trash-can" id="icon"></i></a>
    ''', orderable=False, attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    paid = tables.BooleanColumn(orderable=False, verbose_name='Paid', attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })

    class Meta:
        model = Order
        template_name = 'django_tables2/bootstrap.html'
        fields = ['date', 'title', 'tag_final_value','action', 'paid', 'delete',]

    def render_paid(self, value, record):
        if value:
            return mark_safe(f'''<input type="checkbox" class='paid_button' pk='{record.id}' checked />''')
        else:
            return mark_safe(f'''<input type="checkbox" class='paid_button' pk='{record.id}' />''')


class ProductTable(tables.Table):
    tag_price = tables.Column(orderable=False, verbose_name='Price')
    action = tables.TemplateColumn('''
            <button data-href="{% url "ajax-add" instance.id record.id %}" class="outline secondary add_button" style="border: none; padding-bottom: 0px; cursor: pointer;"><h2 style="color: #005F3D;"><i class="fa-solid fa-square-plus"></i></h2></button>
    ''', orderable=False)

    class Meta:
        model = Tournament
        template_name = 'django_tables2/bootstrap.html'
        fields = ['name', 'tag_price',]

class OrderItemTable(tables.Table):
    tag_price = tables.Column(orderable=False, verbose_name='Price')
    action = tables.TemplateColumn('''
            <button data-href="{% url "ajax-modify" record.id %}" class="outline secondary edit_button" style="border: none; padding-bottom: 0px; cursor: pointer;"><h2 style="color: #AF291D;"><i class="fa-solid fa-square-minus"></i></h2></button>
    ''', orderable=False)

    class Meta:
        model = OrderItem
        template_name = 'django_tables2/bootstrap.html'
        fields = ['tournament', 'qty',]

class InvoiceTable(tables.Table):
    tag_price = tables.Column(orderable=False, verbose_name='Price')

    class Meta:
        model = OrderItem
        template_name = 'django_tables2/bootstrap.html'
        fields = ['tournament', 'qty',]

    
