from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from public.models import Nationalities
from public.serializers import NationalitySerializer
from django.db.models import Q


@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def get_nationality(request):
    name = request.GET.get("name")
    id = request.GET.get("id")
    if name:
        nationalities = Nationalities.objects.filter(
            Q(nicename__istartswith=name) | Q(iso__iexact=name)
        )
        if nationalities.exists():
            serializer = NationalitySerializer(nationalities, many=True)
            return Response(serializer.data, status=200)
        else:
            return Response({"status": "not found"}, status=404)
    elif id:
        nationalities = Nationalities.objects.get(id=id)
        if nationalities:
            serializer = NationalitySerializer(nationalities)
            return Response(serializer.data, status=200)
        else:
            return Response({"status": "not found"}, status=404)
    else:
        return Response({"status": "name parameter missing"}, status=400)
