from django.urls import path

from .api_views import (
    ProposalCreateView,
    ProposalsFromMeListView,
    ProposalStatusUpdateView,
    ProposalsToMeListView,
)
from .views import (
    create_ad,
    delete_ad,
    edit_ad,
    index,
    my_ads_list,
    proposal_create,
    proposals_from_me_view,
    proposals_to_me_view,
    search_ads,
)

urlpatterns = [
    path("", index, name="index"),
    path("my-created-ads", my_ads_list, name="ad_list"),
    path("create/", create_ad, name="ad_create"),
    path("edit/<int:pk>/", edit_ad, name="ad_edit"),
    path("delete/<int:pk>/", delete_ad, name="ad_delete"),
    path("search/", search_ads, name="ad_search"),
    path("proposals/to-me/view/", proposals_to_me_view, name="proposals-to-me-view"),
    path("proposals/from-me/view/", proposals_from_me_view, name="proposals-from-me-view"),
    path("proposal/create/view/", proposal_create, name="proposal_create-view"),
    # API
    path("proposals/to-me/", ProposalsToMeListView.as_view(), name="proposals-to-me"),
    path("proposals/from-me/", ProposalsFromMeListView.as_view(), name="proposals-from-me"),
    path("proposals/create/", ProposalCreateView.as_view(), name="proposals-create"),
    path(
        "proposals/<int:pk>/update-status/",
        ProposalStatusUpdateView.as_view(),
        name="proposal-status-update",
    ),
]
