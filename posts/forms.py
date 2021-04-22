from django import forms
from django.core.files.images import get_image_dimensions

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("title", "text", "group", "image")

    def clean_text(self):
        data = self.cleaned_data["text"]
        if data is None:
            raise forms.ValidationError("Вы ничего не написали!")
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)

    def clean_text(self):
        data = self.cleaned_data["text"]
        if data is None:
            raise forms.ValidationError("Вы ничего не написали!")
        return data
