import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import TestCase
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from shared.middlewares import SlidingAccessTokenMiddleware

User = get_user_model()


def _get_response(_request):
    return HttpResponse("ok")


class SlidingAccessTokenMiddlewareTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            mobile_number="+201234567806", password="123456"
        )

    def test_mints_token_when_near_expiry(self):
        token = AccessToken.for_user(self.user)
        token["tv"] = self.user.token_version
        token["exp"] = int(time.time()) + 10

        request = self.client.request().wsgi_request
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {str(token)}"
        request.user = self.user

        middleware = SlidingAccessTokenMiddleware(_get_response)
        response = middleware(request)

        self.assertIn("X-Access-Token", response)
        new_token = AccessToken(response["X-Access-Token"])
        self.assertEqual(new_token["tv"], self.user.token_version)

    def test_does_not_mint_token_without_authentication(self):
        request = self.client.request().wsgi_request

        middleware = SlidingAccessTokenMiddleware(_get_response)
        response = middleware(request)

        self.assertNotIn("X-Access-Token", response)

    def test_ignores_invalid_token(self):
        request = self.client.request().wsgi_request
        middleware = SlidingAccessTokenMiddleware(_get_response)

        with mock.patch.object(
            middleware.auth, "authenticate", side_effect=TokenError()
        ):
            response = middleware(request)

        self.assertNotIn("X-Access-Token", response)

    def test_skips_when_user_not_authenticated(self):
        request = self.client.request().wsgi_request
        request.user = AnonymousUser()

        middleware = SlidingAccessTokenMiddleware(_get_response)
        with mock.patch.object(
            middleware,
            "_authenticate",
            return_value=(self.user, {"exp": int(time.time()) + 10}),
        ):
            response = middleware(request)

        self.assertNotIn("X-Access-Token", response)

    def test_skips_when_token_has_no_exp(self):
        request = self.client.request().wsgi_request
        request.user = self.user

        middleware = SlidingAccessTokenMiddleware(_get_response)
        with mock.patch.object(
            middleware, "_authenticate", return_value=(self.user, {})
        ):
            response = middleware(request)

        self.assertNotIn("X-Access-Token", response)
