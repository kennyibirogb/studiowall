from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import CommissionRequest,Order 

User = get_user_model()


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("phone", "address")
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}
        
class CommissionForm(forms.ModelForm):
    class Meta:
        model = CommissionRequest
        fields = ["name", "email", "phone", "description", "budget"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)

class CommissionFormWithFiles(CommissionForm):
    references = MultipleFileField(required=False)
