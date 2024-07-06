from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils import timezone
from hr_backend import settings
import os
import uuid
from public.models import Nationalities


def upload_to(instance, filename):
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(settings.INTER_PIC_DIR, new_filename)


def get_default_nationalities():
    return Nationalities.objects.get(id=92)[0]


class Interns(models.Model):
    intern_code = models.CharField(primary_key=True, max_length=25)
    intern_photo = models.ImageField(null=True, blank=True, upload_to=upload_to)
    full_name = models.CharField(blank=False, max_length=50)
    dob = models.DateField()
    job_title = models.CharField(
        max_length=10,
        choices=[("Intern", "Intern"), ("Trainee", "Trainee")],
        default="Intern",
    )
    email = models.EmailField(blank=False, unique=True)
    phone_number = models.CharField(max_length=15)
    institute = models.CharField(max_length=100)
    nationality = models.ForeignKey(Nationalities, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=255, blank=True)
    zip = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(default=timezone.now)
    endDate = models.DateField(default=timezone.now)


@receiver(pre_save, sender=Interns)
def generate_interncode(sender, instance, **kwargs):
    if not instance.intern_code:
        job_title = instance.job_title
        prefix = "IN" if job_title == "IN" else "TR"
        i = 1
        while True:
            intern_code = f"{prefix}-{i:04d}"
            if not Interns.objects.filter(intern_code=intern_code).exists():
                break
            i += 1

        instance.intern_code = intern_code
