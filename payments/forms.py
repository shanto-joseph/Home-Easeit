
# payments/forms.py
from django import forms
from .models import Payment

class PaymentForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect
    )
