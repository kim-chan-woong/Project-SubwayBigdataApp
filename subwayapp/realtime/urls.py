from django.urls import path

from . import views


urlpatterns = [
    path('', views.realtime, name='realtime'),
    path('selectsubwayAjax_realtime_selectSubstanm/', views.selectsubwayAjax_realtime_selectSubstanm, name='selectsubwayAjax_realtime_selectSubstanm'),
    path('selectsubwayAjax_realtime_selectAll/', views.selectsubwayAjax_realtime_selectAll, name='selectsubwayAjax_realtime_selectAll'),
]