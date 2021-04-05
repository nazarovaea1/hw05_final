from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if data is None:
            raise forms.ValidationError("Вы ничего не написали!")
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'class': "form-control", }),
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if data is None:
            raise forms.ValidationError("Вы ничего не написали!")
        return data
