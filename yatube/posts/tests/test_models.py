from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая пост",
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        post_str = post.text
        group = PostModelTest.group
        group_str = group.title
        field_str = {
            post_str: "Тестовая пост",
            group_str: "Тестовая группа",
        }

        for field, expected_value in field_str.items():
            with self.subTest(field=field):
                self.assertEqual(
                    field, expected_value
                )

    def test_verbose_name(self):
        """Verbose_name в полях соответствует ожидаемым"""
        post = self.post
        field_verboses = {
            "text": "Текст поста",
            "group": "Группа",
            "author": "author",
            "pub_date": "Дата публикации",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях соответствует ожидаемым"""
        post = self.post
        field_help_texts = {
            "text": "Введите текст поста",
            "group": "Группа, к которой будет относиться пост"
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
