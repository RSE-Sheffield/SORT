import rest_framework.permissions
import rest_framework.viewsets

import api.serializers
import survey.models


class AnswerViewSet(rest_framework.viewsets.ModelViewSet):
    """
    API endpoints for answers.
    """

    queryset = survey.models.Answer.objects.all()
    serializer_class = api.serializers.AnswerSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated]
