from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserAccessToken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("jti", models.CharField(db_index=True, max_length=255, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField()),
                ("expires_at", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_tokens",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Access token",
                "verbose_name_plural": "Access tokens",
            },
        ),
        migrations.AddIndex(
            model_name="useraccesstoken",
            index=models.Index(
                fields=["user", "expires_at"], name="users_usera_user_id_4d7c1c_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="useraccesstoken",
            index=models.Index(
                fields=["expires_at"], name="users_usera_expires_a9d2a9_idx"
            ),
        ),
    ]
