from .models import FullScan
from django.forms import ModelForm, TextInput, Textarea

class FullScanForm(ModelForm):
    class Meta:
        model = FullScan
        fields = ["domains"]
        widgets = {
            # "status": TextInput(attrs={
            #     'class':"form-control",
            #     'placeholder':"Введите статус"
            # }),
            "domains": Textarea(attrs={
                'class':"form-control",
                'placeholder':"Введите домены через enter"
            })
        }