from django.contrib import admin
from django.utils.html import format_html

from .models import Item, Visitor, CartItem, ItemImage, Order, OrderItem
from .views import send_telegram_message


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1
    fields = ('image', 'is_main', 'order', 'image_preview', 'delete_image')
    readonly_fields = ('image_preview', 'delete_image')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;"'
                ' />',
                obj.image.url
            )
        return 'Нет изображения'
    image_preview.short_description = 'Превью'

    def delete_image(self, obj):
        if obj.pk:
            return format_html(
                '<input type="checkbox" name="delete_images" value="{}" />'
                ' Удалить',
                obj.pk
            )
        return 'Сначала сохраните'
    delete_image.short_description = 'Удаление'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('item', 'price')
    fields = ('item', 'price')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    inlines = [ItemImageInline]
    list_display = ('name', 'updated_at', 'price', 'quantity', 'activity',
                    'main_image_preview')
    list_editable = ('price', 'quantity', 'activity')
    search_fields = ('name', 'description')

    def main_image_preview(self, obj):
        img = obj.main_image
        if img:
            return format_html('<img src="{}" height="50" />', img.image.url)
        return 'Нет изображения'
    main_image_preview.short_description = 'Основное изображение'

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        formset.save_m2m()

        if 'delete_images' in request.POST:
            for image_id in request.POST.getlist('delete_images'):
                try:
                    image = ItemImage.objects.get(pk=image_id)
                    image.delete()
                except ItemImage.DoesNotExist:
                    pass


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('id', 'telegram_id', 'last_visit', 'first_visit',
                    'visit_count')
    list_display_links = None

    actions = None

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('visitor', 'item', 'quantity', 'added_at')
    list_filter = ('visitor', 'added_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'visitor_info', 'status', 'total_amount',
                    'created_at', 'contact_phone')
    list_display_links = ('id', 'uuid', 'visitor_info',)
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'visitor__telegram_id', 'contact_phone', 'email')
    readonly_fields = ('created_at', 'total_amount', 'visitor',
                       'yoomoney_payment_id')
    fieldsets = (
        ('Основная информация', {
            'fields': ('visitor', 'status', 'total_amount', 'created_at',
                       'yoomoney_payment_id')
        }),
        ('Данные ТК', {
            'fields': ('tracking', 'transport_company', 'url')
        }),
        ('Контактные данные', {
            'fields': ('last_name', 'first_name', 'middle_name',
                       'contact_phone', 'email')
        }),
        ('Адрес доставки', {
            'fields': ('postcode', 'region', 'city', 'street', 'house',
                       'apartment')
        }),
        ('Дополнительно', {
            'fields': ('comment',)
        }),
    )
    inlines = (OrderItemInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('visitor')

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Order.objects.get(pk=obj.pk)
            if (
                old_obj.status != obj.status and
                obj.status in ['paid', 'collected', 'sent', 'completed']
            ):
                self.handle_status_change(obj.status, obj)

        super().save_model(request, obj, form, change)

    def handle_status_change(self, status, order):
        if status == 'paid':
            send_telegram_message(
                chat_id=str(order.visitor),
                template_key='paid',
                id=order.id
            )
        elif status == 'sent':
            send_telegram_message(
                chat_id=str(order.visitor),
                template_key='sent',
                id=order.id,
                tracking=order.tracking,
                transport_company=order.transport_company,
                url=order.url
            )
        elif status == 'completed':
            send_telegram_message(
                chat_id=str(order.visitor),
                template_key='completed',
                id=order.id,
            )
