import django_tables2 as tables
from .models import OrderItem, Order
from tournaments.models import Tournament, Entry
from django.utils.safestring import mark_safe
from django_tables2.utils import Accessor, AttributeDict, computed_values
from django.urls import reverse, reverse_lazy


class OrderTable(tables.Table):
    tournament = tables.Column(orderable=False, 
                               verbose_name='Tournament')
    
    qty = tables.Column(orderable=False, 
                        verbose_name='No. Teams',
                        attrs={ 'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    
    tag_total_price = tables.Column(orderable=False, 
                                    verbose_name='Total Cost',
                                    attrs={'th':{'style':'text-align: center;'},
                                            'td':{'style':'text-align: center;'},
                                            })
    
    invoiced = tables.BooleanColumn(orderable=False, verbose_name='Invoiced', attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })

    class Meta:
        model = OrderItem
        template_name = 'django_tables2/bootstrap.html'
        fields = ['tournament', 'qty', 'tag_total_price', 'invoiced']

    def render_invoiced(self, value, bound_column, record):
        if value:
            return mark_safe(f'''<i style="color: green; font-size: 26px;" class="fa-solid fa-check"></i>''')
        else:
            return mark_safe(f'''<i style="color: red; font-size: 24px;" class="fa-solid fa-x"></i>''')

class AdminOrderTable(tables.Table):
    tournament = tables.Column(orderable=False, 
                               verbose_name='Tournament')
    
    tournament__tag_price = tables.Column(orderable=False, 
                                    verbose_name='Entry Price',
                                    attrs={'th':{'style':'text-align: center;'},
                                            'td':{'style':'text-align: center;'},
                                            })
    
    invoiced = tables.BooleanColumn(orderable=False, verbose_name='Invoiced', attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })

    class Meta:
        model = Entry
        template_name = 'django_tables2/bootstrap.html'
        fields = ['tournament', 'tournament__tag_price', 'invoiced']

    def render_invoiced(self, value, record):
        if value:
            return mark_safe(f'''<input type="checkbox" class='invoice_button' pk='{record.id}' checked />''')
        else:
            return mark_safe(f'''<input type="checkbox" class='invoice_button' pk='{record.id}' />''')


class ProductTable(tables.Table):
    tag_price = tables.Column(orderable=False, verbose_name='Price')
    date = tables.DateColumn(format ='d/m/Y')
    name = tables.Column(orderable=False, verbose_name='Event')
    action = tables.TemplateColumn('''
            <button data-href="{% url "ajax-add" instance.id record.id %}" class="outline secondary add_button" style="border: none; padding-bottom: 0px; cursor: pointer;"><h2 style="color: #005F3D;"><i class="fa-solid fa-square-plus"></i></h2></button>
    ''', orderable=False, verbose_name="")

    class Meta:
        model = Tournament
        template_name = 'django_tables2/bootstrap.html'
        fields = ['name', 'date', 'tag_price',]

class OrderItemTable(tables.Table):
    tag_price = tables.Column(orderable=False, verbose_name='Price')
    tournament = tables.Column(orderable=False, verbose_name='Event')
    qty = tables.Column(orderable=False)
    action = tables.TemplateColumn('''
            <button data-href="{% url "ajax-modify" record.id %}" class="outline secondary edit_button" style="border: none; padding-bottom: 0px; cursor: pointer;"><h2 style="color: #AF291D;"><i class="fa-solid fa-square-minus"></i></h2></button>
    ''', orderable=False, verbose_name="")

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

    
