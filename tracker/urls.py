from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('toggle/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('login/', auth_views.LoginView.as_view(
        template_name='tracker/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path("delete/<int:task_id>/", views.delete_task, name="delete_task"),
]
