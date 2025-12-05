from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm

class SignUp(UserCreationForm):
    class Meta:
        model=User
        fields=['username','first_name','last_name','email']

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["username"].widget.attrs['placeholder']='username'
        self.fields["first_name"].widget.attrs['placeholder']='first name' 
        self.fields["last_name"].widget.attrs['placeholder']='last name'
        self.fields["password1"].widget.attrs['placeholder']='password'
        self.fields['password2'].widget.attrs['placeholder']='confirm password'
        self.fields['email'].widget.attrs['placeholder']='email'
        self.fields['password1'].widget.attrs.update({'title':'Must contain at least 8 characters, cannot be numeric only, and must not be a commonly used password.'})
        self.fields['username'].widget.attrs.update({'title':'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'})
        
        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'form-control bg-light  border-0','data-bs-toggle':'tooltip'})
            field.label=''
            field.help_text=None

class login_form(AuthenticationForm):
   def __init__(self,*args,**kwargs):
       super().__init__(*args,**kwargs)
       for fieldname, field in self.fields.items():
           field.widget.attrs.update({'class':'form-control border-0 bg-light'})
            
          
            
            
            