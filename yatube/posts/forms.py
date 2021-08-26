from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')  # русификация в модели
        help_texts = {'text': 'Пиши что-нибудь полезное!',
                      'group': 'И группу выбери',
                      }

    def clean_text(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError(
                'ПИШИ! ПИШИ! ПИШИ!')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )  # русификация в модели

    def clean_text(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError(
                'Пустой текст недопустим')
        return data
