from django.urls import path
from . import views


urlpatterns = [
    path('', views.all, name='all'),
    path('yra/', views.yra, name='yra'),
    path('lra/', views.lra, name='lra'),
    path('nra/', views.nra, name='nra'),
    path('selectsubway/', views.selectsubway, name='selectsubway'),
    path('selectsubwayAjax_batch/', views.selectsubwayAjax_batch, name='selectsubwayAjax_batch'),
]