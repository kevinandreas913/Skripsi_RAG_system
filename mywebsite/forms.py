from django import forms
from .models import TbUser

class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = TbUser
        fields = ['username', 'password', 'gmail']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'id': 'username'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'password': 'password'}),
            'gmail': forms.EmailInput(attrs={'class': 'form-control', 'id': 'gmail'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if TbUser.objects.filter(username=username).exists():
            error = f"{username} sudah digunakan"
            raise forms.ValidationError(error)
        
        return username
    
    def clean_gmail(self):
        gmail = self.cleaned_data.get('gmail')

        if TbUser.objects.filter(gmail=gmail).exists():
            error = f"{gmail} sudah digunakan"
            raise forms.ValidationError(error)
        
        return gmail
    
    def clean_password(self):
        password = self.cleaned_data.get('password')

        if len(password) < 8:
            error = "password harus minimal 8 karakter"
            raise forms.ValidationError(error)
        
        return password
    
