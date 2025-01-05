from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date
import uuid

from decimal import Decimal

from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        # Explicitly set required fields for superuser
        required_fields = {
            'height': 1.75,
            'weight': 70.0 
        }

        for field, value in required_fields.items():
            extra_fields.setdefault(field, value)

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):

    class GenderChoices(models.TextChoices):
        MEN = 'Men', 'Men'
        WOMAN = 'Woman', 'Woman'
        

    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

    email = models.EmailField(null=True, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_trainer = models.BooleanField(blank=True, null=True, default=False, help_text="If you do not check this box, it is assumed that you are a regular user.")
    gender = models.CharField(max_length=6, blank=True, null=True, choices=GenderChoices.choices, default=GenderChoices.MEN)
    date_of_birth = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default-boy-avatar.jpg')

    height = models.DecimalField(
        max_digits=4,  # Maximum 3 digits before the decimal and 1 after (e.g., 2.5 m)
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal(0.50)),
            MaxValueValidator(Decimal(2.50))
        ],
        help_text="Height in meters (e.g., 1.75)."
    )
    weight = models.DecimalField(
        max_digits=5,  # Maximum 3 digits before the decimal and 2 after (e.g., 120.50 kg)
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal(2.00)),
            MaxValueValidator(Decimal(300.00))
        ],
        help_text="Weight in kilograms (e.g., 70.5)."
    )


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()
    
    def save(self, *args, **kwargs):
        self.username = self.email  # username stays synced with email

        # make sure avatar matches gender
        if self.gender == "Woman":
            self.avatar = "avatars/default-girl-avatar.jpg"
        
        super().save(*args, **kwargs)
    
    @property
    def calculate_age(self):
        today = date.today()
        if self.date_of_birth:
            return (
                today.year - self.date_of_birth.year -
                ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            )
        
        return "You didn't fill date_of_birth field"
    
    class Meta:
        verbose_name_plural = _("Users")

    def __str__(self):
        return f"User email: {self.email}"
    
class FitnessGoal(models.Model):
    GOAL_CHOICES = [
        ('Weight Loss', 'Weight Loss'),
        ('Strength Building', 'Strength Building'),
        ('Cardiovascular Fitness', 'Cardiovascular Fitness'),
        ('Flexibility', 'Flexibility'),
        ('BodyBuilding', 'BodyBuilding'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fitness_goals')
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

    goal_type = models.CharField(max_length=35, choices=GOAL_CHOICES)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True, help_text="Optional deadline for the goal")
    description = models.TextField(blank=True, help_text="Additional details about the goal")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = _("Fitness Goals")

    def __str__(self):
        return f"is active: {self.is_active}, goals: {self.goal_type}."