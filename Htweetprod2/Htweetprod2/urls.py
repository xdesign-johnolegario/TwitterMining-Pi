from django.conf.urls import url
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from Htweets2 import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^htweets2/', views.Htweets2List.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)