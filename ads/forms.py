from django import forms
from .models import Ad


class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ['title', 'description', 'image', 'category', 'condition']

        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Введите заголовок объявления',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Подробное описание',
                'rows': 4,
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition resize-none'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition'
            }),
            'category': forms.TextInput(attrs={ 
                'placeholder': 'Введите категорию',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition'
            }),
            'condition': forms.Select(attrs={ 
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition'
            }),
        }
        labels = {
            'title': 'Заголовок',
            'description': 'Описание',
            'image': 'Изображение',
            'category': 'Категория',
            'condition': 'Состояние',
        }
