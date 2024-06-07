from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Patient, Appointment, MedicalRecord, Prescription, Charge
from mpesa.models import PaymentTransaction

# Token generation
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny

# serilizers
from .serializers import (
    PatientSerializer,
    AppointmentSerializer,
    MedicalRecordSerializer,
    PrescriptionSerializer,
    ChargeSerializer,
    AdminUserSerializer,
    UserSerializer,
)
from django.contrib.auth import get_user_model

User = get_user_model()


@api_view(["POST"])
# @permission_classes([IsAdminUser])  # Only allow existing admins to create new admins
@permission_classes([AllowAny])
def create_admin(request):
    serializer = AdminUserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Please provide both username and password"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )

    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": user.role,
        },
        status=status.HTTP_200_OK,
    )


# View for handling patient creation
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_patient(request):
    if request.user.role not in ["receptionist", "admin"]:
        return Response(
            {
                "error": f"Permission denied for user {request.user.username} with role {request.user.role}"
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # Check if patient already exists
    patient_data = request.data
    try:
        patient = Patient.objects.get(
            name=patient_data["name"], phone_number=patient_data["phone_number"]
        )
        return Response(
            {"error": "Patient with these details already exists."},
            status=status.HTTP_409_CONFLICT,
        )
    except Patient.DoesNotExist:
        serializer = PatientSerializer(data=patient_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# View for handling appointment creation
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def book_appointment_for_patient(request, patient_id):
    if request.user.role not in ["receptionist", "admin"]:
        return Response(
            {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )

    try:
        patient = Patient.objects.get(id=patient_id)
        print(f"Patient: {patient}")
    except Patient.DoesNotExist:
        return Response(
            {"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND
        )

    data = request.data.copy()
    data["patient"] = patient.id
    data["booked_by"] = request.user.id  # Set the booked_by field to the current user

    print(f"Request Data: {data}")

    serializer = AppointmentSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        print(f"Serializer Errors: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# view for showing all the patients
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_patients(request):
    if request.user.role not in [
        "receptionist",
        "admin",
        "pharmacist",
        "doctor",
    ]:
        return Response(
            {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )

    patients = Patient.objects.all()
    serializer = PatientSerializer(patients, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_patient(request, patient_id):
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return Response(
            {"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND
        )

    serializer = PatientSerializer(patient)
    return Response(serializer.data, status=status.HTTP_200_OK)


# View for handling medical record creation
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def doctor_appointments(request):
    if request.user.role not in [
        "receptionist",
        "admin",
        "pharmacist",
        "doctor",
    ]:
        return Response(
            {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )

    appointments = Appointment.objects.filter(booked_by=request.user)
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)


# # GEt the appointments each patient have attended and been booked for
# @api_view(["GET"])
# def patient_appointments(request, patient_id):
#     try:
#         patient = Patient.objects.get(id=patient_id)
#     except Patient.DoesNotExist:
#         return Response(status=404)

#     appointments = Appointment.objects.filter(patient=patient)
#     serializer = AppointmentSerializer(appointments, many=True)
#     return Response(serializer.data)


# # Get the patients medical record
# @api_view(["GET"])
# def medical_record_prescriptions(request, medical_record_id):
#     try:
#         medical_record = MedicalRecord.objects.get(id=medical_record_id)
#     except MedicalRecord.DoesNotExist:
#         return Response(status=404)

#     prescriptions = Prescription.objects.filter(medical_record=medical_record)
#     serializer = PrescriptionSerializer(prescriptions, many=True)
#     return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_medical_record(request, patient_id):
    if request.user.role not in [
        "receptionist",
        "admin",
        "pharmacist",
        "doctor",
    ]:
        return Response(
            {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )

    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return Response(
            {"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND
        )

    data = request.data.copy()
    data["patient"] = patient.id
    data["added_by"] = request.user.id

    serializer = MedicalRecordSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_prescription(request, medical_record_id):
    if request.user.role not in [
        "receptionist",
        "admin",
        "pharmacist",
        "doctor",
    ]:
        return Response(
            {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )

    try:
        medical_record = MedicalRecord.objects.get(id=medical_record_id)
    except MedicalRecord.DoesNotExist:
        return Response(
            {"error": "Medical record not found"}, status=status.HTTP_404_NOT_FOUND
        )

    data = request.data.copy()
    data["medical_record"] = medical_record.id
    data["prescribed_by"] = request.user.id

    serializer = PrescriptionSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view("[GET]")
# @permission_classes([IsAuthenticated])
# def show_transactions(request):
#     if request.user.role != "admin":
#         return Response(
#             {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
#         )
