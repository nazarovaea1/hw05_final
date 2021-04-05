import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.test_user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.test_user)
        cls.group = Group.objects.create(title='test_group')

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.test_user,
            group=Group.objects.get(title='test_group'),
        )
        cls.form = PostForm()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTests.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(group=form_data['group'],
                                            text=form_data['text'],
                                            image='posts/small.gif').exists())

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        test_post = self.post
        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTests.group.id,
        }

        response = self.authorized_client.post(
            reverse('post_edit', kwargs={
                'username': self.test_user.username,
                'post_id': test_post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={'username': self.test_user.username,
                            'post_id': test_post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(
            group=form_data['group'],
            text=form_data['text']).exists())


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.test_user)
        cls.form = CommentForm()
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.test_user,)

    def test_create_comment(self):
        """Валидная форма создает комментарий в Post."""
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый текст комментария',
        }
        response = self.authorized_client.post(
            reverse('add_comment', kwargs={
                'username': CommentFormTests.test_user.username,
                'post_id': CommentFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('post', kwargs={
            'username': CommentFormTests.test_user.username,
            'post_id': CommentFormTests.post.id}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=form_data['text'],).exists())
