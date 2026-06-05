from django.db import migrations, models


def drop_image_add_image_data(apps, schema_editor):
    schema_editor.execute(
        "ALTER TABLE checker_attempt DROP COLUMN IF EXISTS image_url;"
    )
    schema_editor.execute(
        "ALTER TABLE checker_attempt DROP COLUMN IF EXISTS image;"
    )
    schema_editor.execute(
        "ALTER TABLE checker_attempt ADD COLUMN image_data bytea NOT NULL DEFAULT ''::bytea;"
    )


class Migration(migrations.Migration):

    dependencies = [
        ('checker', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(drop_image_add_image_data, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='attempt',
                    name='image_url',
                ),
                migrations.AddField(
                    model_name='attempt',
                    name='image_data',
                    field=models.BinaryField(blank=True, default=b''),
                ),
            ],
        ),
    ]
