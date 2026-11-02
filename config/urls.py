
from django.contrib import admin
from django.urls import path
from core.views import inicio, login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inicio, name='inicio'),
    path('login/', login_view, name='login'),
]
