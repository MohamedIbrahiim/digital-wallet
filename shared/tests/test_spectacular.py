from django.test import SimpleTestCase

from shared.auth.spectacular import VersionedJWTAuthenticationExtension


class SpectacularExtensionTests(SimpleTestCase):
    def test_security_definition(self):
        extension = VersionedJWTAuthenticationExtension(target=None)
        definition = extension.get_security_definition(auto_schema=None)

        self.assertEqual(definition["type"], "http")
        self.assertEqual(definition["scheme"], "bearer")
        self.assertEqual(definition["bearerFormat"], "JWT")
