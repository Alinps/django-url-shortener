from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

User = get_user_model()


class SignUp(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")

        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs['placeholder'] = 'username'
        self.fields["password1"].widget.attrs['placeholder'] = 'password'
        self.fields["password2"].widget.attrs['placeholder'] = 'confirm password'
        self.fields["email"].widget.attrs['placeholder'] = 'email'

        self.fields['password1'].widget.attrs.update({
            'title': 'Must contain at least 8 characters, cannot be numeric only, and must not be a commonly used password.'
        })

        self.fields['username'].widget.attrs.update({
            'title': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        })

        for name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control bg-light border-0',
                'data-bs-toggle': 'tooltip'
            })
            field.label = ''
            field.help_text = None


class login_form(AuthenticationForm):
    username = forms.EmailField(label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'placeholder': 'Email',
            'class': 'form-control border-0 bg-light'
        })

        self.fields['password'].widget.attrs.update({
            'placeholder': 'Password',
            'class': 'form-control border-0 bg-light'
        })



