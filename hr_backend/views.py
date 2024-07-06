from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def checkserver(request):
    return JsonResponse({"status": "ok"}, status=200)