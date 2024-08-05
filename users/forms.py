from django import forms
from django.contrib.auth.models import User
from users.models import Profile

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileUpdateForm(forms.ModelForm):
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'No spaces. E.g. 07123456789'}), required=False)

    class Meta:
        model = Profile
        fields = ['invoice_email', 'phone_number',]
