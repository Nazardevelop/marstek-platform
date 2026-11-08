from django.urls import path

from devices import views

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health"),
    path("devices/", views.DeviceListView.as_view(), name="device-list"),
    path("devices/discover/", views.DeviceDiscoverView.as_view(), name="device-discover"),
    path("devices/<int:device_id>/", views.DeviceDetailView.as_view(), name="device-detail"),
    path("devices/<int:device_id>/status/", views.DeviceStatusView.as_view(), name="device-status"),
    path(
        "devices/<int:device_id>/network/",
        views.DeviceNetworkView.as_view(),
        name="device-network",
    ),
    path("devices/<int:device_id>/mode/", views.DeviceModeView.as_view(), name="device-mode"),
    path("devices/<int:device_id>/settings/dod/", views.DodView.as_view(), name="device-dod"),
    path("devices/<int:device_id>/settings/led/", views.LedView.as_view(), name="device-led"),
    path(
        "devices/<int:device_id>/settings/ble-adv/",
        views.BleAdvView.as_view(),
        name="device-ble-adv",
    ),
    path(
        "devices/<int:device_id>/settings/power-version/",
        views.PowerVersionView.as_view(),
        name="device-power-version",
    ),
    path(
        "devices/<int:device_id>/factory-reset/",
        views.FactoryResetView.as_view(),
        name="device-factory-reset",
    ),
]
