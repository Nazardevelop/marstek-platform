from django.urls import path

from stats import views

urlpatterns = [
    path("devices/<int:device_id>/history/", views.HistoryView.as_view(), name="device-history"),
    path(
        "devices/<int:device_id>/energy/daily/",
        views.DailyEnergyView.as_view(),
        name="device-energy-daily",
    ),
]
