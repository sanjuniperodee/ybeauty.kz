import os
import random
import string
import urllib.request
import subprocess
import stripe
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from django.views.decorators.csrf import csrf_exempt

from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm
from .models import Item, OrderItem, Order, Address, Coupon, Refund, UserProfile, Brand


stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, payment=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, payment=False)
            if form.is_valid():
                print("User is entering a new shipping address")
                shipping_address1 = form.cleaned_data.get(
                    'shipping_address')
                shipping_address2 = form.cleaned_data.get(
                    'shipping_address2')
                shipping_country = form.cleaned_data.get(
                    'shipping_country')
                shipping_zip = form.cleaned_data.get('shipping_zip')
                phone_number = form.cleaned_data.get('phone_number')
                if is_valid_form([shipping_address1, shipping_country, shipping_zip, phone_number]):
                    shipping_address = Address(
                        phone_number = phone_number,
                        user=self.request.user,
                        street_address=shipping_address1,
                        apartment_address=shipping_address2,
                        country=shipping_country,
                        zip=shipping_zip,
                        address_type='S'
                    )
                    shipping_address.save()
                    order.shipping_address = shipping_address
                    order.save()

                subprocess.call("php smt.php " + str(order.id) + " " + str(int(order.get_total())), shell=True)
                print(os.path.exists("testfile.txt"))

                content = ""
                with open("testfile.txt") as f:
                    content = f.readlines()
                data = {
                    'pg_order_id': order.id,
                    'pg_merchant_id': "545774",
                    'pg_amount': int(order.get_total()),
                    'pg_description': "test",
                    'pg_salt': "ybeauty",
                    'pg_sig': content,
                    'pg_success_url': 'http://127.0.0.1:8000/successPayment/',
                    'pg_failure_url': 'http://127.0.0.1:8000/checkout/',
                    'pg_success_url_method': 'GET',
                    'pg_failure_url_method': 'GET',
                }
                print(data)
                result = requests.post('https://api.paybox.money/init_payment.php', params=data)
                sg = ""
                result = str(result.text)
                smt = ""
                print(result.__sizeof__())
                print(result)
                for i in range(10, result.__sizeof__()):
                    # print(i)
                    smt+=result[i]
                    print(smt)
                    if result[i] == 'l' and result[i+1] == '>':
                        print('gfdsgdfg')
                        i += 2
                        while result[i] != '<':
                            sg += result[i]
                            i+=1
                        break
                return redirect(sg)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")

def SuccesPayment(request):
    order = Order.objects.get(user=request.user, payment=False)
    order_items = order.items.all()
    order_items.update(ordered=True)
    for item in order_items:
        item.save()
    order.ordered_date = timezone.now()
    order.payment = True
    order.ref_code = create_ref_code()
    order.save()
    messages.success(request, "Your order was successful!")
    return redirect("/")

#
# class PaymentView(View):
#     def get(self, *args, **kwargs):
#         order = Order.objects.get(user=self.request.user, ordered=False)
#         if order.billing_address:
#             context = {
#                 'order': order,
#                 'DISPLAY_COUPON_FORM': False,
#                 'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY
#             }
#             userprofile = self.request.user.userprofile
#             if userprofile.one_click_purchasing:
#                 # fetch the users card list
#                 cards = stripe.Customer.list_sources(
#                     userprofile.stripe_customer_id,
#                     limit=3,
#                     object='card'
#                 )
#                 card_list = cards['data']
#                 if len(card_list) > 0:
#                     # update the context with the default card
#                     context.update({
#                         'card': card_list[0]
#                     })
#             return render(self.request, "payment.html", context)
#         else:
#             messages.warning(
#                 self.request, "You have not added a billing address")
#             return redirect("core:checkout")
#
#     def post(self, *args, **kwargs):
#         order = Order.objects.get(user=self.request.user, ordered=False)
#         form = PaymentForm(self.request.POST)
#         userprofile = UserProfile.objects.get(user=self.request.user)
#         if form.is_valid():
#             token = form.cleaned_data.get('stripeToken')
#             save = form.cleaned_data.get('save')
#             use_default = form.cleaned_data.get('use_default')
#
#             if save:
#                 if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
#                     customer = stripe.Customer.retrieve(
#                         userprofile.stripe_customer_id)
#                     customer.sources.create(source=token)
#
#                 else:
#                     customer = stripe.Customer.create(
#                         email=self.request.user.email,
#                     )
#                     customer.sources.create(source=token)
#                     userprofile.stripe_customer_id = customer['id']
#                     userprofile.one_click_purchasing = True
#                     userprofile.save()
#
#             amount = int(order.get_total() * 100)
#
#             try:
#
#                 if use_default or save:
#                     # charge the customer because we cannot charge the token more than once
#                     charge = stripe.Charge.create(
#                         amount=amount,  # cents
#                         currency="usd",
#                         customer=userprofile.stripe_customer_id
#                     )
#                 else:
#                     # charge once off on the token
#                     charge = stripe.Charge.create(
#                         amount=amount,  # cents
#                         currency="usd",
#                         source=token
#                     )
#
#                 # create the payment
#                 payment = Payment()
#                 payment.stripe_charge_id = charge['id']
#                 payment.user = self.request.user
#                 payment.amount = order.get_total()
#                 payment.save()
#
#                 # assign the payment to the order
#
#                 order_items = order.items.all()
#                 order_items.update(ordered=True)
#                 for item in order_items:
#                     item.save()
#
#                 order.ordered = True
#                 order.payment = payment
#                 order.ref_code = create_ref_code()
#                 order.save()
#
#                 messages.success(self.request, "Your order was successful!")
#                 return redirect("/")
#
#             except stripe.error.CardError as e:
#                 body = e.json_body
#                 err = body.get('error', {})
#                 messages.warning(self.request, f"{err.get('message')}")
#                 return redirect("/")
#
#             except stripe.error.RateLimitError as e:
#                 # Too many requests made to the API too quickly
#                 messages.warning(self.request, "Rate limit error")
#                 return redirect("/")
#
#             except stripe.error.InvalidRequestError as e:
#                 # Invalid parameters were supplied to Stripe's API
#                 print(e)
#                 messages.warning(self.request, "Invalid parameters")
#                 return redirect("/")
#
#             except stripe.error.AuthenticationError as e:
#                 # Authentication with Stripe's API failed
#                 # (maybe you changed API keys recently)
#                 messages.warning(self.request, "Not authenticated")
#                 return redirect("/")
#
#             except stripe.error.APIConnectionError as e:
#                 # Network communication with Stripe failed
#                 messages.warning(self.request, "Network error")
#                 return redirect("/")
#
#             except stripe.error.StripeError as e:
#                 # Display a very generic error to the user, and maybe send
#                 # yourself an email
#                 messages.warning(
#                     self.request, "Something went wrong. You were not charged. Please try again.")
#                 return redirect("/")
#
#             except Exception as e:
#                 # send an email to ourselves
#                 messages.warning(
#                     self.request, "A serious error occurred. We have been notifed.")
#                 return redirect("/")
#
#         messages.warning(self.request, "Invalid data received")
#         return redirect("/payment/stripe/")


class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home.html"


@csrf_exempt
def home1(request, ctg, ctg2):
    object_list = Item.objects.filter(category__title=ctg, category__subcategory__title=ctg2).order_by('title')
    brands = Brand.objects.filter(category__title=ctg, category__subcategory__title=ctg2)
    print(brands)
    brandy = []
    if request.method == 'POST':
        brandy = request.POST.getlist('scales')
        print(brandy)
        object_list = []
        i = 0
        for brand in brandy:
            i+=1
            object_list += Item.objects.filter(category__title=ctg, category__subcategory__title=ctg2, brand__title=brand).order_by('title')
        if i == 0:
            object_list = Item.objects.filter(category__title=ctg, category__subcategory__title=ctg2).order_by('title')
    paginator = Paginator(object_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'brandy': brandy,
        'str1': ctg2,
        'str': ctg,
        'object_list': page_obj,
        'brands': brands,
    }
    return render(request, 'shopping_page.html', context)


@csrf_exempt
def home(request):
    page_obj = Paginator(Item.objects.get_queryset().filter(category__title='Парфюмы').order_by('title'), 4).get_page(request.GET.get('page'))
    page_obj2 = Paginator(Item.objects.get_queryset().filter(category__title='Уход за Кожей').order_by('title'), 4).get_page(request.GET.get('page'))
    page_obj3 = Paginator(Item.objects.get_queryset().filter(category__title='Уход за Волосами').order_by('title'), 4).get_page(request.GET.get('page'))
    page_obj4 = Paginator(Item.objects.get_queryset().filter(category__title='Декоративная Косметика').order_by('title'), 4).get_page(request.GET.get('page'))
    page_obj5 = Paginator(Item.objects.get_queryset().filter(category__title='Подарочный Набор').order_by('title'), 4).get_page(request.GET.get('page'))
    page_obj6 = Paginator(Item.objects.get_queryset().filter(category__title='Для Дома').order_by('title'), 4).get_page(request.GET.get('page'))
    context = {
        'str': 'none',
        'object_list': page_obj,
        'object_list2': page_obj2,
        'object_list3': page_obj3,
        'object_list4': page_obj4,
        'object_list5': page_obj5,
        'object_list6': page_obj6

    }
    return render(request, 'home_page.html', context)


def carousel(request):
    return render(request, 'carousel.html')



@login_required
def order_summary(request):
    try:
        order = Order.objects.get_queryset().filter(user=request.user, payment=False)
        context = {
            'objects': order
        }
        return render(request, 'order_summary.html', context)
    except ObjectDoesNotExist:
        messages.warning(request, "You do not have an active order")
        return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "detail.html"


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False

    )
    order_qs = Order.objects.filter(user=request.user, payment=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        payment=False,
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")
