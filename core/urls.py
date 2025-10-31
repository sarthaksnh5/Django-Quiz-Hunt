from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("question/<uuid:question_id>/", views.question_entrypoint, name="question_entrypoint"),
    path("question/<uuid:question_id>/view/", views.question_detail, name="question_detail"),
    path("question/<uuid:question_id>/submit/", views.submit_answer, name="submit_answer"),
    path("admin/overview/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/users/<slug:nickname>/", views.admin_user_detail, name="admin_user_detail"),
    path("logout/", views.logout_contestant, name="logout"),
]
