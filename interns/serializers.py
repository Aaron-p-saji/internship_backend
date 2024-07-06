from rest_framework import serializers
from .models import Interns

class InternSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interns
        fields = '__all__'
        read_only_fields = ['intern_code']
