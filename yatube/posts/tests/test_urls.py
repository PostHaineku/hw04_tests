from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.shortcuts import get_object_or_404

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = get_object_or_404(User, username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_templates_non_auth(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.post.author}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_exist_for_anonymous(self):
        response = [
            self.guest_client.get('/'),
            self.guest_client.get(f'/group/{self.group.slug}/'),
            self.guest_client.get(f'/profile/{self.post.author}/'),
            self.guest_client.get(f'/posts/{self.post.id}/')
        ]
        for urls in response:
            with self.subTest(urls=urls):
                self.assertEqual(urls.status_code, 200)

    def test_urls_redirect_for_anonimous(self):
        response = [
            self.guest_client.get('/posts/1/edit/'),
            self.guest_client.get('/create/')
        ]
        for urls in response:
            with self.subTest(urls=urls):
                self.assertEqual(urls.status_code, 302)

    def test_urls_exist_for_auth(self):
        response = [
            self.authorized_client.get('/'),
            self.authorized_client.get(f'/group/{self.group.slug}/'),
            self.authorized_client.get(f'/profile/{self.post.author}/'),
            self.authorized_client.get(f'/posts/{self.post.id}/'),
            self.authorized_client.get(f'/posts/{self.post.id}/edit/'),
            self.authorized_client.get('/create/'),
        ]
        for urls in response:
            with self.subTest(urls=urls):
                self.assertEqual(urls.status_code, 200)

    def get_404(self):
        response = self.authorized_client.get('/non_existing_page/')
        self.assertEqual(response.status_code, 404)
