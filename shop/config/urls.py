from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from shop.views import (
    ItemListView,
    ItemDetailView,
    CartAPIView,
    CartItemListView,
    CheckoutFormView,
    OrderDetailView,
    PrivacyPolicyView,
    yookassa_webhook,
    CheckoutErrorTView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', ItemListView.as_view(), name='home'),
    path('item/<slug:slug>/', ItemDetailView.as_view(), name='item_detail'),
    path('cart/', CartItemListView.as_view(), name='cart'),
    path('api/cart/<slug:slug>/', CartAPIView.as_view(), name='cart_del'),
    path('api/cart/', CartAPIView.as_view(), name='cart_api'),
    path('api/yookassa-webhook/', yookassa_webhook, name='yookassa_webhook'),
    path('checkout/', CheckoutFormView.as_view(), name='checkout'),
    path('order/success/<uuid:uuid>/',
         OrderDetailView.as_view(), name='order_success'),
    path('checkout/error/',
         CheckoutErrorTView.as_view(), name='checkout_error'),
    path('privacy-policy/',
         PrivacyPolicyView.as_view(), name='privacy_policy'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'RoSa Shop'
admin.site.index_title = 'Административная панель магазина'
