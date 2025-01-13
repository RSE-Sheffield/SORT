import rest_framework.routers
from django.urls import include, path

import api.views

router = rest_framework.routers.DefaultRouter()
router.register(r"answers", api.views.AnswerViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]
