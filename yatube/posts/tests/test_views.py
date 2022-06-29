from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.shortcuts import get_object_or_404
from ..models import Group, Post, Comment
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import shutil
import tempfile
from django.core.cache import cache

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.user2 = User.objects.create_user(username="auth2")
        cls.user3 = User.objects.create_user(username="auth3")
        cls.group1 = Group.objects.create(
            title="Тестовая группа",
            slug="Test_slug",
            description="Тестовое описание",
        )
        cls.group2 = Group.objects.create(
            title="Тестовая группа",
            slug="Test_slug2",
            description="Тестовое описание",
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post1 = Post.objects.create(
            author=cls.user,
            text="Тестовая пост1",
            group=cls.group1,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            text="Комментарий",
            author=cls.user,
            post=cls.post1
        )

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

    def test_pages_uses_correct_templates(self):
        """URL используют правильные шаблоны"""
        templates_pages_names = {
            reverse("posts:home_page"): "posts/index.html",
            reverse(
                "posts:group_posts", kwargs={"slug": "Test_slug"}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": "auth"}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post1.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post1.id}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html"
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:home_page"))
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object.author, self.post1.author)
        self.assertEqual(first_object.text, self.post1.text)

    def test_group_list_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:group_posts", kwargs={"slug": "Test_slug"})
        )
        self.assertEqual(response.context["title"], self.post1.group.title)
        self.assertEqual(
            response.context["description"], self.post1.group.description
        )
        # не до конца понял ваше замечание тут в прошлый раз

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": "auth"})
        )
        objects = response.context["page_obj"]
        for one_object in objects:
            self.assertEqual(one_object.author, self.post1.author)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post1.id})
        )
        post = response.context["post"]
        self.assertEqual(post.id, self.post1.id)

    def test_edit_post_form(self):
        """Шаблон post_edit формирует форму с правильными полями"""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post1.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_form(self):
        """Шаблон create_post формирует форму с правильными полями"""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_group_post_existance(self):
        """проверка инициализации поста на всех нужных страницах"""
        response = self.authorized_client.get(reverse("posts:home_page"))
        context_posts = response.context["page_obj"]
        self.assertIn(self.post1, context_posts, msg=None)
        response2 = self.authorized_client.get(
            reverse("posts:group_posts", kwargs={"slug": self.group1.slug})
        )
        context_group_posts = response2.context["page_obj"]
        self.assertIn(self.post1, context_group_posts, msg=None)
        response3 = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username})
        )
        context_posts_profile = response3.context["page_obj"]
        self.assertIn(self.post1, context_posts_profile, msg=None)

    def test_images_inside_context(self):
        """Проверка передачи картинок в контексте"""
        response1 = self.authorized_client.get(
            reverse("posts:home_page")
        )
        first_object = response1.context["page_obj"][0]
        self.assertEqual(first_object.image, self.post1.image)
        response2 = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username})
        )
        first_object = response2.context["page_obj"][0]
        self.assertEqual(first_object.image, self.post1.image)
        response3 = self.authorized_client.get(
            reverse("posts:group_posts", kwargs={"slug": self.group1.slug})
        )
        first_object = response3.context["page_obj"][0]
        self.assertEqual(first_object.image, self.post1.image)
        response4 = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post1.id})
        )
        first_object = response4.context["post"]
        self.assertEqual(first_object.image, self.post1.image)

    def test_succesfull_comment(self):
        """Проверка появления комментария в контексте страницы"""
        self.assertEqual(Comment.objects.count(), 1)
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post1.id})
        )
        first_comment = response.context["comments"][0]
        self.assertIn("Комментарий", first_comment.text)

    def test_cache_index(self):
        """Проверка кеша home_page"""
        response = self.authorized_client.get(reverse("posts:home_page"))
        obj = response.context["page_obj"]
        self.assertEqual(len(obj), 1)
        # проверка словаря на 1 пост
        Post.objects.create(
            author=self.user,
            text="Тестовая пост2",
            group=self.group1
        )
        cnt = Post.objects.count()
        # проверка существования второго поста
        self.assertEqual(cnt, 2)
        # проверка сохранения кеша
        self.assertEqual(len(obj), 1)
        cache.clear()
        response2 = self.authorized_client.get(reverse("posts:home_page"))
        obj = response2.context["page_obj"]
        # проверка пересоздания кеша
        self.assertEqual(len(obj), 2)

    def test_follow_unfollow(self):
        """Проверка возможности подписаться и отписаться"""
        self.authorized_client.get(reverse(
            "posts:profile_follow",
            kwargs={"username": "auth2"})
        )
        response1 = self.authorized_client.get(reverse(
            "posts:profile",
            kwargs={"username": "auth2"})
        )
        boolean1 = response1.context["following"]
        self.assertTrue(boolean1)
        self.authorized_client.get(reverse(
            "posts:profile_unfollow",
            kwargs={"username": "auth2"})
        )
        response2 = self.authorized_client.get(reverse(
            "posts:profile",
            kwargs={"username": "auth2"})
        )
        boolean2 = response2.context["following"]
        self.assertFalse(boolean2)

    def test_posts_follow_unfollow(self):
        self.authorized_client.get(reverse(
            "posts:profile_follow",
            kwargs={"username": "auth2"})
        )
        test_post1 = Post.objects.create(
            author=self.user2,
            text="Тестовая пост2",
            group=self.group1
        )
        response1 = self.authorized_client.get(reverse("posts:follow_index"))
        follow_posts1 = response1.context["page_obj"]
        self.assertIn(test_post1, follow_posts1)
        test_post2 = Post.objects.create(
            author=self.user3,
            text="Тестовая пост2",
            group=self.group1
        )
        response2 = self.authorized_client.get(reverse("posts:follow_index"))
        follow_posts2 = response2.context["page_obj"]
        self.assertNotIn(test_post2, follow_posts2)
