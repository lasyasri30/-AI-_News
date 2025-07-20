from django import forms
from .models import UserPreference, Category

class PreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['categories']
        widgets = {
            'categories': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
        }
        labels = {
            'categories': 'Choose your favorite categories'
        }
