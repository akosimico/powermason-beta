# project_profiling/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ProjectCost, ProjectProfile

def update_project_expense(project):
    """Recalculate total expenses for a project"""
    total_expense = sum(cost.amount for cost in project.costs.all())
    project.expense = total_expense
    project.save(update_fields=["expense"])

@receiver(post_save, sender=ProjectCost)
def update_expense_on_save(sender, instance, **kwargs):
    if instance.project:
        update_project_expense(instance.project)

@receiver(post_delete, sender=ProjectCost)
def update_expense_on_delete(sender, instance, **kwargs):
    if instance.project:
        update_project_expense(instance.project)
