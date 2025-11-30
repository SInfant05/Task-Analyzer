# tasks/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Task(models.Model):
    """
    Represents a task with properties for priority calculation.
    
    Attributes:
        title: Brief description of what needs to be done
        due_date: Deadline for the task
        estimated_hours: Expected time to complete (in hours)
        importance: User-defined priority level (1-10 scale)
        dependencies: List of task IDs that must be completed first
    """
    
    title = models.CharField(
        max_length=200,
        help_text="What needs to be done?"
    )
    
    due_date = models.DateField(
        help_text="When is this due?"
    )
    
    estimated_hours = models.PositiveIntegerField(
        default=2,
        validators=[MinValueValidator(1)],
        help_text="How many hours will this take?"
    )
    
    importance = models.PositiveIntegerField(
        default=5,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        help_text="How important is this? (1=low, 10=critical)"
    )
    
    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="List of task IDs that must be done first"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-importance', 'due_date']
    
    def __str__(self):
        return f"{self.title} (Due: {self.due_date}, Importance: {self.importance})"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'estimated_hours': self.estimated_hours,
            'importance': self.importance,
            'dependencies': self.dependencies or [],
        }