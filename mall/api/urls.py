from rest_framework.routers import SimpleRouter
from django.urls import path
from .views import MallCreateAndTenant, MallListWithTenant,MallDelete, MallViewSet,UpdateMallWithTenant,ExistingTenantList

router = SimpleRouter()
router.register(r"", MallViewSet, basename="mall")

urlpatterns = [
    path("malltenantcreate/", MallCreateAndTenant.as_view(), name="mallcreateandtenant"),
    path("malltenantretailread/",MallListWithTenant.as_view(),name='mallretaillist'),
    path("updatemalltenant/<int:pk>/",UpdateMallWithTenant.as_view(),name='mallretaiu[date]'),
    path("deletemall/<int:pk>/",MallDelete.as_view(),name='malldelete]'),
    path("existing-tenants/", ExistingTenantList.as_view(), name="existing-tenants"),

]



urlpatterns += router.urls
