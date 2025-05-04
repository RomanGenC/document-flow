import re

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'last_name', 'email', 'first_name']

    def validate(self, data):
        if data.get('email') and not re.match(r'.+@\w+\.\w+', data.get('email')):
            raise ValidationError('Введите валидный email.')

        return data


class HtmlToPdfConvertSerializer(serializers.Serializer):
    file_content = serializers.CharField(required=True, allow_blank=False)
    file_name = serializers.CharField(
        required=False,
        default='document',
        max_length=100,
    )
