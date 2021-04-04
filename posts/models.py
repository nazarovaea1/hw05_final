import textwrap

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy
from pytils.translit import slugify

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Группа',
                             help_text='Выберите группу',)
    slug = models.SlugField(max_length=100,
                            unique=True, blank=True,)
    description = models.TextField()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:100]
        super().save(*args, **kwargs)


class Post(models.Model):
    text = models.TextField(verbose_name='Текст записи',
                            help_text='Введите текст поста',)
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey(Group, models.SET_NULL, blank=True, null=True,
                              related_name="posts",)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ("-pub_date",)

    def __str__(self):
        return textwrap.shorten(self.text, width=15)  # , self.author


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments")
    text = models.TextField(verbose_name='Текст комментария',
                            help_text='Введите ваш комментарий',)
    created = models.DateTimeField("datetime published", auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following")
    created = models.DateTimeField("datetime started following",
                                   auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='User cant follow someone twice')]
        ordering = ["-created"]

    def __str__(self):
        f"{self.user} follows {self.author}"

    def clean(self):
        if self.user == self.author:
            raise ValidationError({'user_not_author': gettext_lazy(
                'Пользователь не может подписаться сам на себя.')})