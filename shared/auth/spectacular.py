from drf_spectacular.extensions import OpenApiAuthenticationExtension


class VersionedJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "shared.auth.authentication.VersionedJWTAuthentication"
    name = "VersionedJWTAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
