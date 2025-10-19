from django.apps import AppConfig


class ProjectProfilingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'project_profiling'

class ProjectProfilingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project_profiling"

    def ready(self):
        import project_profiling.signals