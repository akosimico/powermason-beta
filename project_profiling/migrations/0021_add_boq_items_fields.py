# Generated manually to add missing BOQ fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project_profiling', '0020_projectprofile_boq_file_processed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectprofile',
            name='boq_items',
            field=models.JSONField(
                blank=True,
                help_text='Detailed BOQ items with dependencies and breakdowns',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='projectprofile',
            name='boq_dependencies',
            field=models.JSONField(
                blank=True,
                help_text='Dependency mapping for BOQ items',
                null=True
            ),
        ),
    ]
