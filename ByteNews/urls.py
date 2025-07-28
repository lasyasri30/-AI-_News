from django.contrib import admin
from django.urls import path, include
from users import views as user_views  # import home view
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    # news app URLs
    path('', include('news.urls')),

    # user registration
    path('users/', include('users.urls')),

    # login/logout URLs (from django.contrib.auth)
    path('accounts/', include('django.contrib.auth.urls')),

    # home view (optional override of empty path)
    path('home/', user_views.home, name='home'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)