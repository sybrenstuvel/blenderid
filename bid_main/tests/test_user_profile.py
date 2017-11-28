from django.test import TestCase


class AutoCreateUserProfileTest(TestCase):
    def test_create_user_happy_flow(self):
        from django.contrib.auth import get_user_model

        user_cls = get_user_model()
        user = user_cls(email='example@example.com',
                        full_name='Dr. Examplović')
        user.save()

        self.assertEqual('Dr. Examplović', user.get_full_name())

        return user
