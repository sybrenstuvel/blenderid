from django.test import TestCase


class AutoCreateUserProfileTest(TestCase):

    def test_create_user_happy_flow(self):
        from django.contrib.auth.models import User

        user = User(username='example',
                    email='example@example.com',
                    first_name='Dr.',
                    last_name='Examplović',
                    )
        user.save()

        self.assertIsNotNone(user.profile)
        self.assertEqual('Dr. Examplović', user.profile.full_name)

        return user

    def test_user_change_profile_name(self):
        user = self.test_create_user_happy_flow()

        user.first_name = ''
        user.last_name = ''
        user.save()

        self.assertEqual('Dr. Examplović', user.profile.full_name)

        user.profile.full_name = 'ဟင်းချို'
        user.profile.save()
        self.assertEqual('ဟင်းချို', user.profile.full_name)
        self.assertEqual('ဟင်းချို', user.first_name)
        self.assertEqual('', user.last_name)

        user.profile.full_name = 'dr. Sybren A. Stüvel'
        user.profile.save()
        self.assertEqual('dr. Sybren A. Stüvel', user.profile.full_name)
        self.assertEqual('dr. Sybren', user.first_name)
        self.assertEqual('A. Stüvel', user.last_name)
