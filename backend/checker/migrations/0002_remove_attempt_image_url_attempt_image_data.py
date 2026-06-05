from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checker', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attempt',
            name='image_url',
        ),
        migrations.AddField(
            model_name='attempt',
            name='image_data',
            field=models.BinaryField(blank=True, default=b''),
        ),
    ]
