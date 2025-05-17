from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        css_class = "w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
        self.fields["username"].widget.attrs.update({"class": css_class, "placeholder": "Логин"})
        self.fields["password"].widget.attrs.update({"class": css_class, "placeholder": "Пароль"})


class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        css_class = "w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update(
                {
                    "class": css_class,
                    "placeholder": self.fields[field_name].label,
                }
            )
