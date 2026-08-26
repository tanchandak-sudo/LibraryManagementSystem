from decimal import Decimal
import requests
from .models import ExchangeRate

ZERO_DECIMAL_CURRENCIES = {'JPY', 'KRW', 'VND', 'XAF', 'XOF', 'XPF', 'CLP', 'PYG'}


def get_exchange_rate(target_currency='USD'):
    """
    Safely retrieves exchange rate from local DB cache.
    If missing, fetches live rates and applies a 2.5% FX buffer.
    """
    target_currency = target_currency.upper()
    if target_currency == 'INR':
        return Decimal('1.0')

    # 1. Try local database cache
    rate_obj = ExchangeRate.objects.filter(currency_code=target_currency).first()
    if rate_obj:
        return rate_obj.rate_from_inr

    # 2. Fetch live rate from exchange rate API
    try:
        url = "https://open.er-api.com/v6/latest/INR"
        response = requests.get(url, timeout=4)
        if response.ok:
            rates = response.json().get('rates', {})
            raw_rate = rates.get(target_currency)
            if raw_rate:
                buffered_rate = Decimal(str(raw_rate)) * Decimal('1.025')
                ExchangeRate.objects.update_or_create(
                    currency_code=target_currency,
                    defaults={'rate_from_inr': buffered_rate}
                )
                return buffered_rate
    except Exception:
        pass

    # 3. Fallbacks if API/DB are unavailable
    fallbacks = {
        'USD': Decimal('0.012'),
        'EUR': Decimal('0.011'),
        'GBP': Decimal('0.0095'),
        'AED': Decimal('0.044'),
    }
    return fallbacks.get(target_currency, Decimal('1.0'))


def get_razorpay_subunits(amount, currency):
    """
    Converts amount to Razorpay integer subunits (e.g., $10.00 -> 1000 cents).
    """
    if currency.upper() in ZERO_DECIMAL_CURRENCIES:
        return int(amount)
    return int(round(Decimal(str(amount)) * 100))


def convert_currency(amount_inr, target_currency='INR'):
    """
    Converts base INR amount into target currency and calculates Razorpay subunits.
    """
    target_currency = target_currency.upper()
    rate = get_exchange_rate(target_currency)
    
    amount_inr_decimal = Decimal(str(amount_inr))
    charged_amount = (amount_inr_decimal * rate).quantize(Decimal('0.01'))
    amount_in_subunits = get_razorpay_subunits(charged_amount, target_currency)
    
    return charged_amount, amount_in_subunits

from django.db.models import Q

def apply_search(queryset, search_query, search_fields):
    """
    Filters a queryset based on a search term across given fields.
    """
    if not search_query:
        return queryset

    query = Q()
    for field in search_fields:
        query |= Q(**{f"{field}__icontains": search_query})
    
    return queryset.filter(query)

