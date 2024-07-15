from rest_framework import serializers
from .models import (
    User,
    Patient,
    Appointment,
    MedicalRecord,
    Prescription,
    PaymentTransaction,
)


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password", "email", "first_name", "last_name"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            is_staff=True,
            is_superuser=True,
            role="admin",
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password", "email", "first_name", "last_name", "role"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            role=validated_data["role"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "id",
            "name",
            "phone_number",
            "added_at",
            "date_of_birth",
        ]


class PatientNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class AppointmentSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    booked_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "appointment_date",
            "status",
            "booked_by",
        ]

    def get_patient_name(self, obj):
        return obj.patient.name


class MedicalRecordSerializer(serializers.ModelSerializer):

    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    added_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "patient",
            "symptoms",
            "diagnosis_date",
            "added_by",
        ]


class PrescriptionSerializer(serializers.ModelSerializer):

    medical_record = serializers.PrimaryKeyRelatedField(
        queryset=MedicalRecord.objects.all()
    )
    prescribed_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())

    class Meta:
        model = Prescription
        fields = [
            "id",
            "patient",
            "medical_record",
            "medication",
            "dosage",
            "prescribed_by",
        ]


class MedicalRecordWithPrescriptionsSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    added_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    prescriptions = PrescriptionSerializer(
        many=True, read_only=True, source="prescription_set"
    )

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "patient",
            "symptoms",
            "diagnosis_date",
            "added_by",
            "prescriptions",
        ]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = "__all__"
