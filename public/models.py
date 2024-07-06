from django.db import models


# Create your models here.
class Nationalities(models.Model):
    id = models.BigAutoField(primary_key=True)
    iso = models.CharField(max_length=2)
    name = models.CharField(max_length=80)
    nicename = models.CharField(max_length=80)
    country_code = models.CharField(max_length=3, null=True, blank=True)
    numcode = models.SmallIntegerField(null=True, blank=True)
    phone_code = models.IntegerField()
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
