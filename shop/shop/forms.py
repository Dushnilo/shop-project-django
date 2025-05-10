from django import forms


class CheckoutForm(forms.Form):
    last_name = forms.CharField(
        label='Фамилия*',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label='Имя*',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    middle_name = forms.CharField(
        label='Отчество',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    contact_phone = forms.CharField(
        label='Телефон*',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (XXX) XXX-XX-XX'
        })
    )
    email = forms.EmailField(
        label='Email*',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    postcode = forms.CharField(
        label='Почтовый индекс*',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    region = forms.CharField(
        label='Регион/Область*',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    city = forms.CharField(
        label='Город/Населенный пункт*',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    street = forms.CharField(
        label='Улица*',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    house = forms.CharField(
        label='Дом*',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    apartment = forms.CharField(
        label='Квартира/Офис',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    comment = forms.CharField(
        label='Комментарии к заказу',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ваши пожелания по заказу...'
        })
    )

    def clean_contact_phone(self):
        phone = self.cleaned_data['contact_phone']
        if len(phone) < 5:
            raise forms.ValidationError('Введите корректный номер телефона')
        return phone
