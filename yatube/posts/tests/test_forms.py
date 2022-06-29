from django.test import Client, TestCase
from django.urls import reverse
from ..models import Post, Comment
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from ..forms import PostForm
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from http import HTTPStatus
import shutil
import tempfile
from django.core.cache import cache

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.post1 = Post.objects.create(
            author=cls.user,
            text="Тестовая пост1",
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = get_object_or_404(User, username="auth")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Тест добавления поста в БД"""
        posts_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif"
        )
        form_data = {
            "text": "Это тестовый тест",
            "image": uploaded
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post(self):
        """Тест изменения текста после редактирования"""
        form_data = {
            "text": "Это тестовый тест после теста"
        }
        post_for_edit = Post.objects.get(id=self.post1.id)
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": post_for_edit.id}),
            data=form_data,
            follow=True
        )
        post_edit = Post.objects.get(id=self.post1.id)
        self.assertEqual(post_for_edit.author, self.user)
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post1.id})
        )
        self.assertEqual(post_edit.text, "Это тестовый тест после теста")

    def test_comment_non_auth(self):
        """
        тест на невозможность комментирования
        неавторизованным пользователем
        """
        comments_count = Comment.objects.count()
        form_data = {
            "text": "Это очень хорошая попытка"
        }
        post = Post.objects.get(id=self.post1.id)
        response = self.guest_client.post(
            reverse("posts:post_detail", kwargs={"post_id": post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count)
