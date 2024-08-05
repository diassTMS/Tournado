from django import forms
from django.contrib.auth.models import User
from tournaments.models import Tournament
import datetime

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username','email']



        