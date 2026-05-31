from django import forms
from .models import ProductReview, ContactMessage

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'review', 'name', 'email']
        widgets = {
            'rating': forms.Select(choices=[(5, '5 - Excellent'), (4, '4 - Good'), (3, '3 - Average'), (2, '2 - Poor'), (1, '1 - Terrible')]),
            'review': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address_line1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address_line2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    zip_code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_to_different = forms.BooleanField(required=False)
    shipping_first_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    shipping_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_address_line1 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_address_line2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_country = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_state = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_zip_code = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    payment_method = forms.ChoiceField(choices=[
        ('mpesa', 'M-Pesa'),
        ('paypal', 'Paypal'),
        ('direct_check', 'Direct Check'),
        ('bank_transfer', 'Bank Transfer'),
    ], widget=forms.RadioSelect(attrs={'class': 'custom-control-input'}))
    mpesa_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'e.g. 0712 345 678',
    }))
