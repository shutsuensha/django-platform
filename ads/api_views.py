from rest_framework import generics, permissions, filters
from .models import ExchangeProposal
from .serializers import ProposalCreateSerializer, ProposalStatusUpdateSerializer
from django_filters.rest_framework import DjangoFilterBackend

class ProposalCreateView(generics.CreateAPIView):
    queryset = ExchangeProposal.objects.all()
    serializer_class = ProposalCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


# 1 — Список предложений, адресованных мне (моим объявлениям)
class ProposalsToMeListView(generics.ListAPIView):
    serializer_class = ProposalCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExchangeProposal.objects.filter(ad_receiver__user=self.request.user)
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['ad_sender', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


# 2 — Список предложений, которые я отправил (от моих объявлений)
class ProposalsFromMeListView(generics.ListAPIView):
    serializer_class = ProposalCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExchangeProposal.objects.filter(ad_sender__user=self.request.user)
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['ad_receiver', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class ProposalStatusUpdateView(generics.UpdateAPIView):
    queryset = ExchangeProposal.objects.all()
    serializer_class = ProposalStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['patch']

    def get_object(self):
        obj = super().get_object()
        if obj.ad_receiver.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Вы не можете изменить статус этого предложения.")
        return obj