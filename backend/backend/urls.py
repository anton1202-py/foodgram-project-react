from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.authtoken import views

urlpatterns = (path('admin/', admin.site.urls),
               path('api/', include('api.urls', namespace='api')),
               path('redoc/', TemplateView.as_view(template_name='redoc.html'),
                    name='redoc'),
               path('api/auth/token/login/', views.obtain_auth_token),
               )