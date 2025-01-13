# Django REST framework serializers
# These are used to convert our models into data, such as JSON format.

import rest_framework.serializers

import survey.models


class AnswerSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    class Meta:
        model = survey.models.Answer
        fields = '__all__'
