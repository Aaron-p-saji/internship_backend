from rest_framework import serializers
from .models import Nationalities


class NationalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Nationalities
        fields = "__all__"
