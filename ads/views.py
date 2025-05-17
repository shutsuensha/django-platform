from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import AdForm
from .models import Ad, ExchangeProposal
from django.db.models import Q
from django.core.paginator import Paginator


@login_required
def index(request):
    ads = Ad.objects.all().order_by('-created_at')
    paginator = Paginator(ads, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'index.html', {'page_obj': page_obj})


@login_required
def my_ads_list(request):
    ads = Ad.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_ads_list.html', {'ads': ads})


@login_required
def create_ad(request):
    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES)  
        if form.is_valid():
            ad = form.save(commit=False)
            ad.user = request.user
            ad.save()
            return redirect('index') 
    else:
        form = AdForm()
    return render(request, 'create_ad.html', {'form': form})


@login_required
def edit_ad(request, pk):
    try:
        ad = Ad.objects.get(pk=pk)
    except Ad.DoesNotExist:
        return render(request, 'not_found_ad.html', status=404)

    if ad.user != request.user:
        return render(request, 'forbidden_ad.html', status=403)

    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = AdForm(instance=ad)

    return render(request, 'edit_ad.html', {'form': form, 'ad': ad})


@login_required
def delete_ad(request, pk):
    try:
        ad = Ad.objects.get(pk=pk)
    except Ad.DoesNotExist:
        return render(request, 'not_found_ad.html', status=404)

    if ad.user != request.user:
        return render(request, 'forbidden_ad.html', status=403)

    if request.method == 'POST':
        ad.delete()
        return redirect('index')

    return render(request, 'delete_ad.html', {'ad': ad})


@login_required
def search_ads(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    condition = request.GET.get('condition', '')

    ads = Ad.objects.all()

    if query:
        ads = ads.filter(Q(title__icontains=query) | Q(description__icontains=query))
    
    if category:
        ads = ads.filter(category__iexact=category)
    
    if condition:
        ads = ads.filter(condition__iexact=condition)

    ads = ads.order_by('-created_at')

    paginator = Paginator(ads, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)



    context = {
        'query': query,
        'category': category,
        'condition': condition,
        'page_obj': page_obj,
    }
    return render(request, 'search.html', context)


@login_required
def proposals_to_me_view(request):
    proposals = ExchangeProposal.objects.filter(ad_receiver__user=request.user)
    status = request.GET.get('status')
    sender_id = request.GET.get('sender')

    if status:
        proposals = proposals.filter(status=status)
    if sender_id:
        proposals = proposals.filter(ad_sender__user__id=sender_id)

    proposals = proposals.order_by('-created_at')

    senders = (
        ExchangeProposal.objects
        .filter(ad_receiver__user=request.user)
        .values('ad_sender__user__id', 'ad_sender__user__username')
        .distinct()
    )

    return render(request, 'proposals_to_me.html', {
        'proposals': proposals,
        'senders': senders,
        'selected_status': status,
        'selected_sender': sender_id,
    })


@login_required
def proposals_from_me_view(request):
    proposals = ExchangeProposal.objects.filter(ad_sender__user=request.user)
    status = request.GET.get('status')
    receiver_id = request.GET.get('receiver')

    if status:
        proposals = proposals.filter(status=status)
    if receiver_id:
        proposals = proposals.filter(ad_receiver__user__id=receiver_id)

    proposals = proposals.order_by('-created_at')

    receivers = (
        ExchangeProposal.objects
        .filter(ad_sender__user=request.user)
        .values('ad_receiver__user__id', 'ad_receiver__user__username')
        .distinct()
    )

    return render(request, 'proposals_from_me.html', {
        'proposals': proposals,
        'receivers': receivers,
        'selected_status': status,
        'selected_receiver': receiver_id,
    })


@login_required
def proposal_create(request):
    ad_receiver_id = request.GET.get('ad_receiver')
    ad_receiver = get_object_or_404(Ad, pk=ad_receiver_id)

    user_ads = Ad.objects.filter(user=request.user).exclude(pk=ad_receiver.pk)

    if request.method == 'POST':
        ad_sender_id = request.POST.get('ad_sender')
        comment = request.POST.get('comment', '').strip()

        ad_sender = get_object_or_404(Ad, pk=ad_sender_id, user=request.user)

        proposal = ExchangeProposal.objects.create(
            ad_sender=ad_sender,
            ad_receiver=ad_receiver,
            comment=comment,
            status='pending'
        )

        messages.success(request, 'Предложение обмена успешно создано.')
        return redirect('proposals-from-me-view')

    return render(request, 'proposal_create.html', {
        'ad_receiver': ad_receiver,
        'user_ads': user_ads,
    })