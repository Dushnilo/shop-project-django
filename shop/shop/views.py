import ipaddress
import json
import jwt
import os
import requests
import uuid
from django.conf import settings
from django.http import FileResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, FormView, TemplateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView, View
from yookassa import Configuration, Payment

from .forms import CheckoutForm
from .models import Item, Visitor, CartItem, Order, OrderItem
from .serializers import CartItemSerializer

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def decode_token(request):
    token = request.COOKIES.get('jwt_token')
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        visitor, _ = Visitor.objects.get_or_create(
            telegram_id=payload['chat_id'])
        return visitor
    except jwt.InvalidTokenError:
        raise ValueError(status=401)


def send_telegram_message(chat_id, template_key, **kwargs):
    token = settings.TELEGRAM_BOT_TOKEN
    text = settings.MESSAGE_TEMPLATES[template_key]
    text = text.format(**kwargs)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': int(chat_id),
        'text': text,
        'parse_mode': 'Markdown'
    }
    requests.post(url, json=payload)


def is_ip_trusted(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in settings.TRUSTED_YOOKASSA_IPS:
            if ip in ipaddress.ip_network(network):
                return True
        return False
    except ValueError:
        return False


@csrf_exempt
def yookassa_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    client_ip = request.META.get('HTTP_X_REAL_IP')
    '''
    client_ip = (
        request.META.get('HTTP_X_REAL_IP') or
        (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()) or
        request.META.get('REMOTE_ADDR')
    )
    '''
    if not client_ip:
        print('В HTTP_X_REAL_IP нет IP адреса', flush=True)
        return HttpResponse(status=403)

    if not is_ip_trusted(client_ip):
        print(f"Доступ запрещен с IP: {client_ip}", flush=True)
        return HttpResponse(status=403)

    data = json.loads(request.body)
    payment_status = data.get('object', {}).get('status')
    order_id = data.get('object', {}).get('metadata', {}).get('order_id')

    if not order_id:
        return HttpResponse(status=404)

    order = Order.objects.get(id=order_id)
    if payment_status == 'succeeded':
        order.status = 'paid'
        order.save()

        send_telegram_message(chat_id=str(order.visitor),
                              template_key='paid', id=order.id)

        order_items = OrderItem.objects.filter(order_id=order_id)
        deactivate_ids = order_items.values_list('item_id', flat=True)
        Item.objects.filter(id__in=deactivate_ids).update(activity=False)
        CartItem.objects.filter(
            visitor=order.visitor,
            item_id__in=deactivate_ids
        ).delete()
    elif payment_status in ['canceled', 'failed']:
        order.status = 'cancelled'
        order.save()

    return HttpResponse(status=200)


class ItemListView(ListView):
    model = Item
    template_name = 'index.html'
    context_object_name = 'items'
    paginate_by = 9

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.template_name = 'items_partial.html'
            return super().get(request, *args, **kwargs)

        response = super().get(request, *args, **kwargs)
        authorized = False
        jwt_token = request.GET.get('token')
        if jwt_token:
            try:
                payload = jwt.decode(
                    jwt_token, settings.SECRET_KEY, algorithms=['HS256'])
                visitor, _ = Visitor.objects.get_or_create(
                    telegram_id=payload['chat_id'])
                visitor.update_visit()
                authorized = True

                response.set_cookie(
                    key='jwt_token',
                    value=jwt_token,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    path='/',
                    domain=None
                )
            except jwt.PyJWTError as e:
                print(f"Invalid JWT: {str(e)}", flush=True)
        else:
            visitor = decode_token(request)
            authorized = True if visitor else False

        response.context_data['authorized'] = authorized
        return response

    def get_queryset(self):
        return Item.objects.filter(activity=True)


class ItemDetailView(DetailView):
    model = Item
    template_name = 'item_detail.html'
    context_object_name = 'item'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = self.object.images.all().order_by(
            '-is_main', 'order')

        visitor = decode_token(self.request)
        if not visitor:
            cart_status = 'unauthorized'
        elif CartItem.objects.filter(visitor=visitor,
                                     item=self.object).exists():
            cart_status = 'in_cart'
        else:
            cart_status = 'not_in_cart'

        context['cart_status'] = cart_status
        return context


class CartItemListView(ListView):
    model = CartItem
    template_name = 'cart.html'
    context_object_name = 'cart_items'

    def dispatch(self, request, *args, **kwargs):
        self.visitor = decode_token(request)
        if not self.visitor:
            return HttpResponse(status=404)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(visitor=self.visitor)


class CartAPIView(APIView):
    def get(self, request):
        visitor = decode_token(request)
        if not visitor:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        cart_items = (CartItem.objects.filter(visitor=visitor)
                      .select_related('item'))
        serializer = CartItemSerializer(cart_items, many=True)
        total = sum(item.item.price
                    for item in cart_items if item.item.activity)

        return Response({
            'items': serializer.data,
            'total': total
        })

    def post(self, request):
        try:
            visitor = decode_token(request)
            slug = request.data.get('slug')
            if not slug or not isinstance(slug, str):
                return Response(status=400)

            item = get_object_or_404(Item, slug=slug, activity=True)

            cart_item, created = CartItem.objects.get_or_create(
                visitor=visitor, item=item)

            if not created:
                return Response(
                    {'error': 'Этот товар уже в вашей корзине'},
                    status=400
                )

            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data, status=201)

        except Item.DoesNotExist:
            return Response(
                {'error': 'Товар не найден'},
                status=404
            )
        except Exception:
            return Response(status=500)

    def delete(self, request, slug=None):
        try:
            visitor = decode_token(request)
            item = get_object_or_404(Item, slug=slug)
            cart_item = get_object_or_404(CartItem, visitor=visitor, item=item)
            cart_item.delete()
            return Response(status=204)
        except Exception:
            return Response(status=400)


class CheckoutFormView(FormView):
    template_name = 'checkout.html'
    form_class = CheckoutForm

    def dispatch(self, request, *args, **kwargs):
        self.visitor = decode_token(request)
        if not self.visitor:
            return redirect('cart')

        cart_items = (CartItem.objects.filter(visitor=self.visitor)
                      .select_related('item'))
        active_items = [item for item in cart_items if item.item.activity]

        if not active_items:
            return redirect('cart')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items = (CartItem.objects.filter(visitor=self.visitor)
                      .select_related('item'))
        context['cart_items'] = cart_items
        context['total'] = sum(item.item.price
                               for item in cart_items
                               if item.item.activity)
        return context

    def form_valid(self, form):
        cart_items = (CartItem.objects.filter(visitor=self.visitor)
                      .select_related('item'))
        active_items = [item for item in cart_items if item.item.activity]

        total_amount = sum(item.item.price for item in active_items)

        order = Order.objects.create(
            visitor=self.visitor,
            total_amount=total_amount,
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            middle_name=form.cleaned_data['middle_name'],
            contact_phone=form.cleaned_data['contact_phone'],
            email=form.cleaned_data['email'],
            postcode=form.cleaned_data['postcode'],
            region=form.cleaned_data['region'],
            city=form.cleaned_data['city'],
            street=form.cleaned_data['street'],
            house=form.cleaned_data['house'],
            apartment=form.cleaned_data['apartment'],
            comment=form.cleaned_data['comment'],
            status='pending'
        )

        for cart_item in active_items:
            OrderItem.objects.create(
                order=order,
                item=cart_item.item,
                price=cart_item.item.price
            )

        return_url = f"{settings.SITE_URL}/order/success/{order.uuid}/"
        payment_dict = {
            'amount': {'value': str(total_amount), 'currency': 'RUB'},
            'confirmation': {'type': 'redirect', 'return_url': return_url},
            'capture': True,
            'description': f"Оплата заказа #{order.id}",
            'metadata': {'order_id': order.id}
        }
        try:
            payment = Payment.create(payment_dict, str(uuid.uuid4()))
            if not payment or not hasattr(payment, 'confirmation'):
                return redirect('checkout_error')
        except Exception:
            return redirect('checkout_error')

        order.yoomoney_payment_id = payment.id
        order.save()

        return redirect(payment.confirmation.confirmation_url)


class OrderDetailView(DetailView):
    model = Order
    template_name = 'order_success.html'
    context_object_name = 'order'

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            return redirect('cart')
        return super().get(request, *args, **kwargs)

    def get_object(self):
        visitor = decode_token(self.request)
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Order, visitor=visitor,
                                 uuid=uuid, status='paid')


class CheckoutErrorTView(TemplateView):
    template_name = 'checkout_error.html'

    def get(self, request, *args, **kwargs):
        visitor = decode_token(request)
        if not visitor:
            return HttpResponse(status=404)
        return self.render_to_response({})


class PrivacyPolicyView(View):
    def get(self, request):
        file_path = os.path.join(settings.BASE_DIR,
                                 'templates', 'docs', 'privacy_policy.pdf')
        return FileResponse(open(file_path, 'rb'),
                            content_type='application/pdf')
