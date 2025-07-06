from django import forms
from django.forms.models import ModelForm

from .models import LANG_CHOICES,Snippet, Comment
from django.contrib.auth.models import User

class SnippetForm(forms.ModelForm):
    class Meta:
        model=Snippet
        fields = ['name', 'lang', 'code', 'public']
        widgets = {
            'name': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "SnippetName"
            }),
            'lang': forms.Select(
                choices=LANG_CHOICES,
                attrs={'class': 'form-control'}
            ),
            'code': forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Введите ваш код здесь"
            }),
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        if len(name) < 5:
            raise forms.ValidationError('Name too short')
        return name

class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email',]
        widgets = {
            'username': forms.TextInput(attrs={'class':'form-control', 'placeholder':'username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email'})
        }
    password1 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class':'form-control','placeholder':'password'}
    ))
    password2 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class':'form-control','placeholder':'confirm password'}
    ))

    def clean_password2(self):
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 and password2 and password1 == password2:
            return password2
        raise forms.ValidationError("Incorrect validation password")


    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class CommentForm(ModelForm):
   class Meta:
      model = Comment
      fields = ['text']