# ไฟล์: my/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # สั่งให้วิ่งไปหาไฟล์ urls.py ที่เราเพิ่งสร้างใน scheduler
    path('api/', include('scheduler.urls')), 
]