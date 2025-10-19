# Generated manually to add missing project_role field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project_profiling', '0021_add_boq_items_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectprofile',
            name='project_role',
            field=models.CharField(
                choices=[
                    ('general_contractor', 'General Contractor'),
                    ('subcontractor', 'Subcontractor')
                ],
                default='general_contractor',
                help_text='Role of the company in this project',
                max_length=20
            ),
        ),
    ]
