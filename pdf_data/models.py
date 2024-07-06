import datetime
from django.db import models

class UserPDF(models.Model):
    user_id = models.CharField(max_length=100)
    filename = models.CharField(max_length=100)
    created_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id} - {self.filename}"
