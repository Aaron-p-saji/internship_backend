from hr_backend import settings
from rest_framework import serializers
from pdf_data.utils import generate_pdf_thumbnail
from .models import UserPDF
from django.urls import reverse


class PDFUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    user_id = serializers.CharField(max_length=100)

class UserPDFSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = UserPDF
        fields = "__all__"

    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                reverse('thumbnail', args=[obj.filename])
            )
        return None