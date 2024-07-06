from django.urls import path, re_path
from .views import check_email, getProfilePic, InternView

urlpatterns = [
    path('intern/', InternView.as_view(), name='intern-create'),
    path('check_email', check_email),
    path('get_profile_pic', getProfilePic)
]
