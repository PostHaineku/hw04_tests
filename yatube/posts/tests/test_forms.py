from django.test import Client, TestCase
from django.urls import reverse
from ..models import Post
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from ..forms import PostForm

User = get_user_model()


class PostsCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='Тестовая пост1',
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.user = get_object_or_404(User, username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Это тестовый тест'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post(self):
        form_data = {
            'text': 'Это тестовый тест после теста'
        }
        post_for_edit = Post.objects.get(id=self.post1.id)
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_for_edit.id}),
            data=form_data,
            follow=True
        )
        post_edit = Post.objects.get(id=self.post1.id)
        self.assertEqual(post_for_edit.author, self.user)
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={'post_id': self.post1.id})
        )
        self.assertEqual(post_edit.text, 'Это тестовый тест после теста')
