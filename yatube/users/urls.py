from django.urls import path

from . import views

# app_name = 'users'

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),

    path('password_change/', views.ChangePassword.as_view(),
         name='password_change'),

    path('password_change/done/', views.ChangePasswordDone.as_view(),
         name='password_change_done'),

    path('password_reset/', views.ResetPassword.as_view(),
         name='password_reset'),

    path('password_reset/done/', views.ResetPasswordDone.as_view(),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         views.ResetPasswordConfirm.as_view(),
         name='password_reset_confirm'),

    path('reset/done/', views.ResetPasswordConfirmDone.as_view(),
         name='password_confirm_done'),

    path('login/', views.Login.as_view(),
         name='login'),

    path('logout/', views.Logout.as_view(),
         name='logout')
]
