from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:id>', views.detail, name='detail'),
    path('success/', views.payment_sucess_view, name='sucess'),
    path('failed/', views.payment_failed_view, name='failed'),
    path('api/checkout-session/<int:id>/', views.create_checkout_session, name='api_checkout_session'),
    path('download/<int:id>/', views.download_file, name='download_file'),
    path('rate/<int:id>/', views.rate_product, name='rate_product'),
    path('createproduct/', views.create_product, name='createproduct'),
    path('editproduct/<int:id>/', views.product_edit, name='editproduct'),
    path('delete/<int:id>/', views.product_delete, name='delete'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='myapp/login.html'), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('invalid/', views.invalid, name='invalid'),
    path('purchases/', views.my_purchases, name='purchase'),
    path('sales/', views.sales, name='sales'),
    path('switch-mode/', views.switch_mode, name='switch_mode'),
]
