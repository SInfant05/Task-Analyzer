from django.contrib import admin
from django.urls import path, include
from tasks.views import IndexView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/tasks/', include('tasks.urls')),
    path('', IndexView.as_view(), name='index'),
]
