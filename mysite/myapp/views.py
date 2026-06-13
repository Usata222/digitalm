import json
import os
from django.http import JsonResponse, HttpResponseNotFound, FileResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import Product, OrderDetail, Rating
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import stripe
from .forms import ProductForm, UserRegistrationForm
from django.db.models import Sum, Q
import datetime


# ── Mode toggle ───────────────────────────────────────────────────────────────

def switch_mode(request):
    current = request.session.get('mode', 'buyer')
    if current == 'buyer':
        request.session['mode'] = 'creator'
        return redirect('dashboard')
    else:
        request.session['mode'] = 'buyer'
        return redirect('index')


# ── Public views ──────────────────────────────────────────────────────────────

def index(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.all()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    return render(request, 'myapp/index.html', {'products': products, 'query': query})


def detail(request, id):
    product = Product.objects.get(id=id)
    stripe_publishable_key = settings.STRIPE_PUBLISHABLE_KEY
    return render(request, 'myapp/detail.html', {
        'product': product,
        'STRIPE_PUBLISHABLE_KEY': stripe_publishable_key,
    })


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            next_url = request.GET.get('next') or request.POST.get('next') or 'login'
            return redirect(next_url)
    else:
        user_form = UserRegistrationForm()
    return render(request, 'myapp/register.html', {
        'user_form': user_form,
        'next': request.GET.get('next', ''),
    })


def invalid(request):
    return render(request, 'myapp/invalid.html')


# ── Auth ──────────────────────────────────────────────────────────────────────

def user_logout(request):
    logout(request)
    return redirect('index')


# ── Stripe / payments ─────────────────────────────────────────────────────────

@csrf_exempt
def create_checkout_session(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required'}, status=401)

    request_data = json.loads(request.body)
    product = Product.objects.get(id=id)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_session = stripe.checkout.Session.create(
        customer_email=request_data['email'],
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': product.name},
                    'unit_amount': int(product.price * 100),
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('sucess')) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(reverse('failed')),
    )

    OrderDetail.objects.create(
        customer=request.user,
        customer_email=request_data['email'],
        product=product,
        amount=product.price,
        session_id=checkout_session['id'],
    )
    return JsonResponse({'sessionId': checkout_session.id, 'url': checkout_session.url})


def payment_sucess_view(request):
    session_id = request.GET.get('session_id')
    if session_id is None:
        return HttpResponseNotFound()

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.checkout.Session.retrieve(session_id)

    order = get_object_or_404(OrderDetail, session_id=session_id)
    if not order.has_paid:
        order.has_paid = True
        order.save()
        product = order.product
        product.total_sales_amount += int(product.price)
        product.total_sales += 1
        product.save()

    return render(request, 'myapp/payment_sucess.html', {'order': order})


def payment_failed_view(request):
    return render(request, 'myapp/failed.html')


# ── File download (buyers only) ───────────────────────────────────────────────

@login_required(login_url='login')
def download_file(request, id):
    """Serve the product file only to users who have a paid order for it."""
    product = get_object_or_404(Product, id=id)
    has_purchased = OrderDetail.objects.filter(
        customer=request.user,
        product=product,
        has_paid=True,
    ).exists()

    if not has_purchased:
        raise Http404("You have not purchased this product.")

    file_path = product.file.path
    if not os.path.exists(file_path):
        raise Http404("File not found.")

    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response


# ── Rating ────────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def rate_product(request, id):
    """Create or update a rating. Only buyers who paid can rate."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    product = get_object_or_404(Product, id=id)

    has_purchased = OrderDetail.objects.filter(
        customer=request.user,
        product=product,
        has_paid=True,
    ).exists()

    if not has_purchased:
        return JsonResponse({'error': 'You must purchase this product to rate it.'}, status=403)

    try:
        stars = int(request.POST.get('stars', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid rating.'}, status=400)

    if stars < 1 or stars > 5:
        return JsonResponse({'error': 'Rating must be between 1 and 5.'}, status=400)

    # update_or_create handles the one-rating-per-user-per-product rule
    rating, created = Rating.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={'stars': stars},
    )

    return JsonResponse({
        'success': True,
        'stars': rating.stars,
        'average': product.average_rating(),
        'count': product.rating_count(),
    })


# ── Product management (creator only) ────────────────────────────────────────

@login_required(login_url='login')
def create_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)
        if product_form.is_valid():
            new_product = product_form.save(commit=False)
            new_product.seller = request.user
            new_product.save()
            return redirect('dashboard')
    else:
        product_form = ProductForm()
    return render(request, 'myapp/create_product.html', {'product_form': product_form})


@login_required(login_url='login')
def product_edit(request, id):
    product = get_object_or_404(Product, id=id)
    if product.seller != request.user:
        return redirect('invalid')

    product_form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and product_form.is_valid():
        product_form.save()
        return redirect('dashboard')

    return render(request, 'myapp/product_edit.html', {
        'product_form': product_form,
        'product': product,
    })


@login_required(login_url='login')
def product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    if product.seller != request.user:
        return redirect('invalid')
    if request.method == 'POST':
        product.delete()
        return redirect('dashboard')
    return render(request, 'myapp/delete.html', {'product': product})


# ── Seller dashboard & analytics ──────────────────────────────────────────────

@login_required(login_url='login')
def dashboard(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, 'myapp/dashboard.html', {'products': products})


@login_required(login_url='login')
def sales(request):
    base_qs = OrderDetail.objects.filter(product__seller=request.user, has_paid=True)

    total_sales = base_qs.aggregate(total=Sum('amount'))

    last_year = datetime.date.today() - datetime.timedelta(days=365)
    yearly_sales = base_qs.filter(created_on__date__gte=last_year).aggregate(total=Sum('amount'))

    last_month = datetime.date.today() - datetime.timedelta(days=30)
    monthly_sales = base_qs.filter(created_on__date__gte=last_month).aggregate(total=Sum('amount'))

    last_week = datetime.date.today() - datetime.timedelta(days=7)
    weekly_sales = base_qs.filter(created_on__date__gte=last_week).aggregate(total=Sum('amount'))

    daily_sales_sums = (
        base_qs
        .values('created_on__date')
        .order_by('created_on__date')
        .annotate(sum=Sum('amount'))
    )

    product_sales_sums = (
        base_qs
        .values('product__name')
        .order_by('product__name')
        .annotate(sum=Sum('amount'))
    )

    return render(request, 'myapp/sales.html', {
        'total_sales': total_sales,
        'yearly_sales': yearly_sales,
        'monthly_sales': monthly_sales,
        'weekly_sales': weekly_sales,
        'daily_sales_sums': daily_sales_sums,
        'product_sales_sums': product_sales_sums,
    })


# ── Buyer purchases ───────────────────────────────────────────────────────────

@login_required(login_url='login')
def my_purchases(request):
    orders = OrderDetail.objects.filter(
        customer=request.user,
        has_paid=True,
    ).select_related('product')

    # Build a dict of product_id → existing rating for this user
    rated_product_ids = Rating.objects.filter(
        user=request.user,
        product__in=[o.product for o in orders],
    ).values_list('product_id', 'stars')
    user_ratings = {product_id: stars for product_id, stars in rated_product_ids}

    # Attach user's existing rating to each order for the template
    orders_with_ratings = []
    for order in orders:
        orders_with_ratings.append({
            'order': order,
            'user_rating': user_ratings.get(order.product.id),
        })

    return render(request, 'myapp/purchases.html', {
        'orders_with_ratings': orders_with_ratings,
    })
