from django import forms
from django.contrib.auth.models import User
from django.forms import modelformset_factory

from .models import Document, DocumentAccess


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file', 'title', 'description']


class PersonalAccountDocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'file_type', 'file_size', 'version', 'status']


DocumentFormSet = modelformset_factory(
    Document,
    form=PersonalAccountDocumentForm,
    extra=0,
)


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Введите пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают')

        return cd['password2']


class GiveAccessForm(forms.ModelForm):
    class Meta:
        model = DocumentAccess
        fields = ['user', 'permissions']
        widgets = {
            'permissions': forms.RadioSelect
        }

    def __init__(self, *args, **kwargs):
        document = kwargs.pop('document')
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.none()

        existing_users = document.accesses.values_list('user_id', flat=True)
        self.fields['user'].queryset = User.objects.exclude(
            id__in=existing_users
        ).exclude(id=document.owner_id)

        self.fields['permissions'].label = 'Уровень доступа'
        self.fields['permissions'].choices = DocumentAccess.ACCESS_LEVELS
