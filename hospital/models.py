from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


# Custom User model
class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("doctor", "Doctor"),
        ("pharmacist", "Pharmacist"),
        ("receptionist", "Receptionist"),
    )

    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username

    groups = models.ManyToManyField(
        Group,
        related_name="hospital_user_set",  # Custom related_name to avoid clash
        blank=True,
        help_text=(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_query_name="hospital_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="hospital_user_permissions_set",  # Custom related_name to avoid clash
        blank=True,
        help_text="Specific permissions for this user.",
        related_query_name="hospital_user_permission",
    )


# Patient model
class Patient(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return self.name


# Appointment model
class Appointment(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment_date = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING
    )
    booked_by = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"role": "receptionist"}
    )

    def __str__(self):
        return f"Appointment for {self.patient.name} on {self.appointment_date}"


# MedicalRecord model
class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    symptoms = models.TextField()
    diagnosis_date = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"role": "doctor"}
    )

    def __str__(self):
        return f"Medical Record for {self.patient.name} on {self.diagnosis_date}"


# Prescription model
class Prescription(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE)
    medication = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    prescribed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"role": "doctor"}
    )

    def __str__(self):
        return f"Prescription for {self.medical_record.patient.name} by {self.prescribed_by.username}"


# Charge model
class Charge(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    charged_by = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"role": "pharmacist"}
    )

    def __str__(self):
        return f"Charge for {self.prescription.medical_record.patient.name} - ${self.amount}"
