from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='test_user')
        cls.test_author = User.objects.create_user(username='test_author')
        cls.authorized_client = Client()
        cls.authorized_client_author = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_author.force_login(cls.test_author)
        cls.group = Group.objects.create(title='test_group',
                                         slug='test-slug',
                                         description='Тест-описание группы',)

        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.test_author,
        )
        cls.public_templates_url_names = {
            "index.html": "/",
            "profile.html": f"/{cls.test_author.username}/",
            "post.html": f"/{cls.test_author.username}/{cls.post.id}/",
            "group.html": f"/group/{cls.group.slug}/",
        }
        cls.private_templates_url_names = {
            "new.html": "/new",
            "post.html": f"/{cls.test_author.username}/{cls.post.id}/comment/",
            "follow.html": "/follow/",
        }

    def test_public_urls_exist_at_desired_location_for_anon_user(self):
        """Общедоступные страницы доступны любому пользователю."""
        for reverse_name in self.public_templates_url_names.values():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_public_urls_exist_at_desired_location_for_auth_user(self):
        """Общедоступные страницы доступны авторизованному пользователю."""
        for reverse_name in self.public_templates_url_names.values():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_private_urls_exist_at_desired_location_for_auth_user(self):
        """Приватные страницы доступны авторизованному пользователю."""
        for reverse_name in self.private_templates_url_names.values():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница post_edit не доступна анонимному пользователю."""
        response = self.guest_client.get(
            f"/{self.user.username}/{self.post.id}/edit")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница post_edit доступна авторизованному автору поста."""
        response = self.authorized_client_author.get(
            f"/{self.user.username}/{self.post.id}/edit")
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница post_edit не доступна авторизованному не автору поста,
        происходит редирект."""
        response = self.authorized_client.get(
            f"/{self.test_author.username}/{self.post.id}/edit/", follow=True)
        self.assertRedirects(
            response, f"/{self.test_author.username}/{self.post.id}/")

    def test_new_url_redirect_anonymous_on_home_page(self):
        """Страница /new/ перенаправляет анонимного пользователя
         на страницу авторизации."""
        response = self.guest_client.get("/new", follow=True)
        self.assertRedirects(
            response, "/auth/login/?next=/new")

    def test_add_comment_url_exists_at_desired_location(self):
        """Страница add_comment не доступна неавторизованному пользователю,
        происходит редирект."""
        response = self.guest_client.get(
            f"/{self.test_author.username}/{self.post.id}/comment/",
            follow=True)
        self.assertRedirects(
            response, "/auth/login/?next=/test_author/1/comment/")

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.public_templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_not_found_returns_404(self):
        response = self.guest_client.get("group/test-slug/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
