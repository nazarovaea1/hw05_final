import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.test_user = User.objects.create_user(username='test_user')
        cls.test_user2 = User.objects.create_user(username='test_user2')
        cls.test_author = User.objects.create_user(username='test_author')
        cls.authorized_client = Client()
        cls.authorized_client2 = Client()
        cls.authorized_author = Client()
        cls.authorized_client.force_login(cls.test_user)
        cls.authorized_client2.force_login(cls.test_user2)
        cls.authorized_author.force_login(cls.test_author)

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

        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.test_user,
            group=cls.group,
            image=cls.uploaded,
        )
        # cls.comment = Comment.objects.create(
        #     text='Тестовый текст поста',
        #     author=cls.test_author,
        # )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def get_post_and_check(self, post):
        self.assertEqual(post.text, PostPagesTests.post.text)
        self.assertEqual(post.pub_date, PostPagesTests.post.pub_date)
        self.assertEqual(post.author, PostPagesTests.post.author)
        self.assertEqual(post.group, PostPagesTests.group)
        self.assertEqual(post.image, PostPagesTests.post.image)

    def test_new_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_add_comment_shows_correct_context(self):
        """Шаблон new_comment сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('add_comment', kwargs={
            'username': PostPagesTests.test_user.username,
            'post_id': PostPagesTests.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context["page"][0]
        return (self.get_post_and_check(first_object))

    def test_group_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(response.context['group'].title,
                         'Тестовое название группы')
        self.assertEqual(response.context['group'].description,
                         'Тестовое описание группы')
        self.assertEqual(response.context['group'].slug, 'test-slug')

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('profile',
                                              kwargs={'username': 'test_user'})
                                              )
        first_object = response.context["page"][0]
        return (self.get_post_and_check(first_object))

    def test_post_page_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post', kwargs={
                'username': PostPagesTests.test_user.username,
                'post_id': PostPagesTests.post.id})
        )
        first_object = response.context["post"]
        return (self.get_post_and_check(first_object))

    def test_group_post_appear_twice(self):
        """При создании поста с указанием группы, пост появляется на главной
        странице и странице выбранной группы."""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context["page"][0]
        return (self.get_post_and_check(first_object))
        response1 = self.authorized_client.get(
            reverse('group', kwargs={'slug': 'test-slug'}))
        group_object = response1.context["page"][0]
        return (self.get_post_and_check(group_object))

    def test_auth_user_can_follow(self):
        """Авторизованный пользователь может подписываться на других."""
        count1 = Follow.objects.count()
        self.authorized_client.get(reverse(
            'profile_follow', kwargs={'username': 'test_author'}))
        count2 = Follow.objects.all().count()
        self.assertEqual(count2, count1 + 1)

    def test_auth_user_can_unfollow(self):
        """Авторизованный пользователь может отписываться от других."""
        self.authorized_client.get(reverse(
            'profile_follow', kwargs={'username': 'test_author'}))
        count1 = Follow.objects.all().count()
        self.authorized_client.get(reverse(
            'profile_unfollow', kwargs={'username': 'test_author'}))
        count2 = Follow.objects.all().count()
        self.assertEqual(count2, count1 - 1)

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех, кто на
        него подписан и не появляется в ленте тех, кто не подписан на него."""
        self.authorized_client.get(reverse(
            'profile_follow', kwargs={'username': 'test_author'}))
        self.author_post = Post.objects.create(
            text='Пост для подписчиков от автора1',
            author=self.test_author,
        )
        response = self.authorized_client.get(reverse(
            'follow_index'))
        self.assertContains(response, self.author_post.text)
        response1 = self.authorized_client2.get(reverse(
            'follow_index'))
        self.assertFalse(response1.context['page'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='test_user')
        cls.POSTS_COUNT = 13
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        Post.objects.bulk_create([Post(
            text=f'Тестовое сообщение{i}',
            author=cls.user,
            group=cls.group)
            for i in range(cls.POSTS_COUNT)])

        cls.get_parameters = {
            'page': 2,
        }
        for page, page_number in cls.get_parameters.items():
            def test_first_index_page_containse_ten_records(self):
                response = self.client.get(reverse('index'))
                self.assertEqual(len(response.context.get(
                    'page').object_list), 10)

            def test_second_index_page_containse_three_records(self):
                response = self.client.get(reverse(
                    'index') + '?page=page_number')
                self.assertEqual(len(response.context.get(
                    'page').object_list), 3)

            def test_first_profile_page_containse_ten_records(self):
                response = self.client.get(reverse(
                    'profile', kwargs={'username': 'test_user'}))
                self.assertEqual(len(response.context.get(
                    'page').object_list), 10)

            def test_second_profile_page_containse_three_records(self):
                response = self.client.get(reverse(
                    'profile', kwargs={'username': 'test_user'}
                ) + '?page=page_number')
                self.assertEqual(len(response.context.get(
                    'page').object_list), 3)

            def test_first_group_page_containse_ten_records(self):
                response = self.client.get(reverse(
                    'group', kwargs={'slug': 'test-slug'}))
                self.assertEqual(len(response.context.get(
                    'page').object_list), 10)

            def test_second_group_page_containse_three_records(self):
                response = self.client.get(reverse(
                    'group', kwargs={'slug': 'test-slug'}
                ) + '?page=page_number')
                self.assertEqual(len(response.context.get(
                    'page').object_list), 3)


class CacheTest(TestCase):
    def test_cache_index_page(self):
        client = Client()
        user = User.objects.create(username='test_user')
        Post.objects.create(
            text='Test_text',
            author=user,
        )
        temp_response = client.get(reverse('index'))
        Post.objects.create(
            text='Test1_text',
            author=user,
        )
        response = client.get(reverse('index'))
        self.assertEqual(temp_response.content, response.content)
