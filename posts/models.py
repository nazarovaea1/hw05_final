import textwrap

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from pytils.translit import slugify

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name="Группа",
                             help_text="Выберите группу",)
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
    title = models.TextField(default="Новый пост",
                             verbose_name="Название поста",
                             help_text="Введите название поста",)
    text = models.TextField(verbose_name="Текст записи",
                            help_text="Введите текст поста",)
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey(Group, models.SET_NULL, blank=True, null=True,
                              related_name="posts",)
    image = models.ImageField(upload_to="posts/", blank=True, null=True)

    class Meta:
        ordering = ("-pub_date",)

    def __str__(self):
        return textwrap.shorten(self.text, width=15)  # , self.author


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments")
    text = models.TextField(verbose_name="Текст комментария",
                            help_text="Введите ваш комментарий",
                            blank=False, null=False)
    created = models.DateTimeField("datetime published", auto_now_add=True)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return f"{self.author} commented: {self.text}"


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following")
    created = models.DateTimeField("datetime started following",
                                   auto_now_add=True, db_index=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=("user", "author",),
                                    name="User cant follow someone twice"),)
        ordering = ("-created",)

    def __str__(self):
        return f"{self.user} follows {self.author}"


# class UserProfile(models.Model):
#     # for user in User.objects.all():
#     # UserProfile.objects.get_or_create(user=user)
#     SEX_CHOICES = (
#         ("m", "Man"),
#         ("f", "Woman"),
#     )
#     MARITAL_STATUS_CHOICES = (
#         ("s", "Single"),
#         ("m", "Married"),
#         ("d", "Divorced"),
#         ("w", "Widowed"),
#     )

#     user = models.OneToOneField(User, on_delete=models.CASCADE)

#     @receiver(post_save, sender=User)
#     def create_user_profile(sender, instance, created, **kwargs):
#         if created:
#             UserProfile.objects.create(user=instance)

#     @receiver(post_save, sender=User)
#     def save_user_profile(sender, instance, **kwargs):
#         instance.profile.save()

    # avatar = models.ImageField()

    # birth_date = models.DateField()
    # sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    # address = models.CharField(max_length=150)
    # postal_code = models.PositiveIntegerField()
    # locatity = models.CharField(max_length=30)
    # marital_status = models.CharField(
    #     max_length=1,
    #     choices=MARITAL_STATUS_CHOICES)
    # child_amount = models.PositiveSmallIntegerField()
    # is_merchant = models.BooleanField(default=False)

    # def create_user_profile(sender, instance, created, **kwargs):
    #     if created:
    #         UserProfile.objects.create(user=instance)
    # def create_user_profile(sender,**kwargs ):
    #     if kwargs['created']:
    #         user_profile=UserProfile.objects.create(user=kwargs['instance'])


# post_save.connect(create_profile,sender=User)
