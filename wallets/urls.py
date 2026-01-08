from django.urls import include, path
from rest_framework.routers import DefaultRouter
from wallets.apis import WalletViewSet

router = DefaultRouter()
router.register(r"wallets", WalletViewSet, basename="wallets")

urlpatterns = [
    path("", include(router.urls)),
]
