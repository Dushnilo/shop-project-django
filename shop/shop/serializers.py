from rest_framework import serializers

from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_slug = serializers.CharField(source='item.slug', read_only=True)
    item_price = serializers.FloatField(source='item.price', read_only=True)
    item_activity = serializers.BooleanField(source='item.activity',
                                             read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'item_name', 'item_slug', 'item_price',
                  'item_activity', 'added_at']
        extra_kwargs = {
            'item': {'write_only': True},
            'added_at': {'read_only': True}
        }
