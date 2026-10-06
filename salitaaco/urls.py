"""
URL configuration for the salitaaco project.

Every logged-in page lives under /dashboard/ (see routes/dashboard/__init__.py).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from .routes import auth, dashboard

urlpatterns = [
    path('', auth.index_view, name="index"),
    path('login/', auth.login_view, name="login"),
    path('register/', auth.register_view, name="register"),
    path('logout/', auth.logout_view, name="logout"),
    path('dashboard/', include(dashboard.urlpatterns)),

    # Address of the PHP application, kept so old bookmarks still arrive.
    re_path(r'^home/?$', RedirectView.as_view(pattern_name='board')),
]

if settings.SHOW_ADMIN_ROUTES:
    # Django's own admin site, at its usual address.
    urlpatterns += [path('admin/', admin.site.urls)]
else:
    # The PHP application's admin dashboard was at /admin; send old bookmarks to the new one.
    urlpatterns += [re_path(r'^admin/?$', RedirectView.as_view(pattern_name='analytics'))]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler400 = 'salitaaco.routes.error_handler.bad_request'
handler403 = 'salitaaco.routes.error_handler.permission_denied'
handler404 = 'salitaaco.routes.error_handler.page_not_found'
handler500 = 'salitaaco.routes.error_handler.server_error'
