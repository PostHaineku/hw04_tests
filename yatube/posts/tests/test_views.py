from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.shortcuts import get_object_or_404
from ..models import Group, Post

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
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
        cls.post1 = Post.objects.create(
            author=cls.user,
            text="Тестовая пост1",
            group=cls.group1
        )

    def setUp(self):
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
