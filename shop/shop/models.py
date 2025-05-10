import os
import uuid
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse


def random_filename(instance, filename):
    ext = os.path.splitext(filename)[1]
    new_filename = f'{uuid.uuid4().hex}{ext}'
    return os.path.join('images/', new_filename)


class Item(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название товара')
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name='URL-идентификатор'
    )
    description = models.TextField(verbose_name='Описание', blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена'
    )
    quantity = models.PositiveIntegerField(verbose_name='Количество на складе')
    activity = models.BooleanField(default=False, verbose_name='Активен')
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата последнего изменения'
    )

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('item_detail', kwargs={'slug': self.slug})

    @property
    def main_image(self):
        return self.images.filter(is_main=True).first() or self.images.first()


class ItemImage(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Товар'
    )
    image = models.ImageField(
        upload_to=random_filename,
        verbose_name='Изображение'
    )
    is_main = models.BooleanField(
        default=False,
        verbose_name='Основное изображение'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['order', 'id']

    def __str__(self):
        return f'Изображение {self.id} для {self.item.name}'

    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)


@receiver(post_delete, sender=ItemImage)
def delete_image_file(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        try:
            os.remove(instance.image.path)
        except Exception as e:
            print(f'Ошибка при удалении файла: {e}')


class Visitor(models.Model):
    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name='Telegram ID'
    )
    first_visit = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Первое посещение'
    )
    last_visit = models.DateTimeField(
        auto_now=True,
        verbose_name='Последнее посещение'
    )
    visit_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество посещений'
    )

    class Meta:
        verbose_name = 'Посетитель'
        verbose_name_plural = 'Посетители'

    def __str__(self):
        return str(self.telegram_id)

    def update_visit(self):
        self.visit_count += 1
        self.save(update_fields=['visit_count', 'last_visit'])


class CartItem(models.Model):
    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Посетитель'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Количество'
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления'
    )

    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        unique_together = ('visitor', 'item')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.item.name} в корзине {self.visitor}'

    @property
    def total_price(self):
        return self.item.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает оплаты'),
        ('cancelled', 'Платеж отменен'),
        ('paid', 'Оплачен'),
        ('collected', 'Заказ собран'),
        ('sent', 'Отправлен'),
        ('completed', 'Доставлен'),
    )

    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Покупатель'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='UUID для ссылки'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус'
    )
    tracking = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Трек посылки'
    )
    transport_company = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Транспортная компания'
    )
    url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Ссылка для отслеживания'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма заказа'
    )
    yoomoney_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID платежа ЮMoney'
    )

    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Отчество'
    )
    contact_phone = models.CharField(
        max_length=20,
        verbose_name='Контактный телефон'
    )
    email = models.EmailField(verbose_name='Email')
    postcode = models.CharField(max_length=20, verbose_name='Почтовый индекс')
    region = models.CharField(max_length=100, verbose_name='Регион/Область')
    city = models.CharField(
        max_length=100,
        verbose_name='Город/Населенный пункт'
    )
    street = models.CharField(max_length=100, verbose_name='Улица')
    house = models.CharField(max_length=20, verbose_name='Дом')
    apartment = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Квартира/Офис'
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Комментарий к заказу'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.id} от {self.created_at.strftime("%d.%m.%Y")}'

    def get_full_address(self):
        address_parts = [
            f'{self.postcode},' if self.postcode else '',
            f'{self.region} обл.,' if self.region else '',
            f'г. {self.city},' if self.city else '',
            f'ул. {self.street},' if self.street else '',
            f'д. {self.house},' if self.house else '',
            f'кв. {self.apartment}' if self.apartment else ''
        ]
        return ' '.join(part for part in address_parts if part).strip(', ')

    def visitor_info(self):
        return f'{self.last_name} {self.first_name}'
    visitor_info.short_description = 'Покупатель'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name='Товар'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена'
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return self.item.name

    def admin_display(self):
        return f'{self.item.name} - {self.price} ₽'
    admin_display.short_description = 'Товар'
