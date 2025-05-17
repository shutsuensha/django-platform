from rest_framework import serializers
from .models import ExchangeProposal
from rest_framework.exceptions import ValidationError


class ProposalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeProposal
        fields = '__all__'
        read_only_fields = ['status', 'created_at'] 

    def validate(self, data):
        user = self.context['request'].user
        ad_sender = data.get('ad_sender')
        ad_receiver = data.get('ad_receiver')

        if ad_sender.user != user:
            raise ValidationError("Вы можете отправлять обмены только от своих объявлений (ad_sender).")

        if ad_receiver.user == user:
            raise ValidationError("Вы не можете отправлять обмены на свои объявления (ad_receiver).")

        return data


class ProposalStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeProposal
        fields = '__all__'
        read_only_fields = ['created_at', 'ad_sender', 'ad_receiver', 'comment'] 

    def validate(self, data):
        status_value = data.get('status')
        allowed_statuses = ['accepted', 'rejected']

        if status_value not in allowed_statuses:
            raise ValidationError("Недопустимый статус. Разрешены только 'accepted' или 'rejected'.")

        return data