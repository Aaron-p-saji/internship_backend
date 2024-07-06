import django.db
from django.http import JsonResponse 
import os
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from hr_backend.settings import BASE_DIR, INTER_PIC_DIR, MEDIA_ROOT
import string
from .models import Interns
from django.db.models import Q
from .serializers import InternSerializer
from rest_framework.decorators import api_view
from PIL import Image
import io
from  django.http import HttpResponse
import base64
import mimetypes

class InternView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if "all" in request.query_params:
            all_interns = Interns.objects.all()
            serializer = InternSerializer(all_interns, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif "id" in request.query_params:
            intern = get_object_or_404(Interns, pk=request.query_params.get("id"))
            serializer = InternSerializer(intern)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif "search" in request.query_params:
            search_query = request.query_params.get("search")
            interns = Interns.objects.filter(
                Q(full_name__icontains=search_query) | Q(email__icontains=search_query)
            )
            serializer = InternSerializer(interns, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response("Not Enough Parameters", status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, *args, **kwargs):
        serializer = InternSerializer(data=request.data)
        if serializer.is_valid():
            save = serializer.save()
            if save:
                return Response("Intern Created", status=status.HTTP_201_CREATED)
            else:
                return Response("Internal Server Error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        intern_id = request.data.get('intern_code')
        if intern_id:
            intern = get_object_or_404(Interns, pk=intern_id)
            serializer = InternSerializer(intern, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response("Intern Data Updated", status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("intern_code is required", status=status.HTTP_400_BAD_REQUEST)  # Import the Interns model from your app

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def check_email(request):
    email = request.GET.get('email')
    if email:
        try:
            intern = Interns.objects.get(email=email)
            return JsonResponse({"status": "email found"}, status=200)
        except Interns.DoesNotExist:
            return JsonResponse({"status": "email not found"}, status=200)
    else:
        return JsonResponse({"status": "email parameter missing"}, status=400)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def getProfilePic(request):
    id = request.GET.get('id')

    if not id:
        return Response({"detail": "ID parameter is missing."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        intern = Interns.objects.get(intern_code=id)
    except Interns.DoesNotExist:
        return Response({"detail": "Intern not found."}, status=status.HTTP_404_NOT_FOUND)
    
    if not intern.intern_photo:
        return Response({"detail": "Intern has no photo."}, status=status.HTTP_404_NOT_FOUND)

    try:
        p = str(intern.intern_photo.name).replace('/', '\\')
        img_path = os.path.join(MEDIA_ROOT, p)
        print(img_path)
        img = Image.open(img_path)
        mime_type = mimetypes.guess_type(img_path)[0] or 'image/png'  # Guess MIME type

        # Convert image to base64
        with open(img_path, "rb") as image_file:
            base64_encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        base64_image_uri = f"data:{mime_type};base64,{base64_encoded_image}"

        return JsonResponse({"base64_image": base64_image_uri})

    except FileNotFoundError:
        return Response({"detail": "Photo file not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"detail": "Thumbnail generation failed.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)