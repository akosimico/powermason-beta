from django.test import TestCase
from authentication.models import UserProfile
from authentication.utils.tokens import get_user_profile, verify_user_profile
from django.contrib.auth.models import User
from django.test import RequestFactory

class SessionAuthTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="bob_test", password="test123")
        cls.profile, _ = UserProfile.objects.get_or_create(
            user=cls.user, defaults={"full_name": "Bob Builder", "role": "OM"}
        )
        cls.factory = RequestFactory()

    def test_get_user_profile_success(self):
        request = self.factory.get('/')
        request.user = self.user
        profile = get_user_profile(request)
        self.assertEqual(profile, self.profile)

    def test_get_user_profile_unauthenticated(self):
        request = self.factory.get('/')
        request.user = User()  # Anonymous user
        profile = get_user_profile(request)
        self.assertIsNone(profile)

    def test_verify_user_profile_success(self):
        request = self.factory.get('/')
        request.user = self.user
        profile = verify_user_profile(request, expected_role='OM')
        self.assertEqual(profile, self.profile)

    def test_verify_user_profile_wrong_role(self):
        request = self.factory.get('/')
        request.user = self.user
        profile = verify_user_profile(request, expected_role='PM')
        self.assertIsNone(profile)