from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import CustomAuthenticationForm

urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html", authentication_form=CustomAuthenticationForm
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
