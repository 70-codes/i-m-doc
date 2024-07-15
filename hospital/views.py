from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Count, Sum
import requests
from django.http import JsonResponse
import base64
from datetime import datetime
import json
from .models import (
    Patient,
    Appointment,
    MedicalRecord,
    PaymentTransaction,
    Prescription,
)

# Token generation
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny

# serilizers
from .serializers import (
    MedicalRecordWithPrescriptionsSerializer,
    PatientSerializer,
    AppointmentSerializer,
    MedicalRecordSerializer,
    PrescriptionSerializer,
    AdminUserSerializer,
    UserSerializer,
    PaymentTransactionSerializer,
)
from .generate_mpesa_access_token import get_access_token
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
    data["booked_by"] = request.user.id

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


# Get user names using the user-id attribute
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_name(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user)
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

    appointments = Appointment.objects.all()
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)


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
    if request.user.role not in ["receptionist", "admin", "pharmacist", "doctor"]:
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

    data["patient"] = medical_record.patient.id

    serializer = PrescriptionSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_patient_full_name(request, patient_id):
    try:
        patient = Patient.objects.get(id=patient_id)
        full_name = patient.name
        return JsonResponse({"full_name": full_name}, status=200)
    except Patient.DoesNotExist:
        return JsonResponse({"error": "Patient not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_prescriptions(request):
    if request.user.role not in [
        "receptionist",
        "admin",
        "pharmacist",
        "doctor",
    ]:
        return Response(
            {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )

    prescriptions = Prescription.objects.all()
    serializer = PrescriptionSerializer(prescriptions, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_stk_push(request, patient_id):
    try:
        print("Received request with patient_id:", patient_id)
        amount = request.data.get("amount")
        phone_number = request.data.get("phone")

        patient = Patient.objects.get(id=patient_id)

        access_token = get_access_token()
        if not access_token:
            return Response(
                {"error": "Failed to retrieve access token"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        business_short_code = "174379"
        process_request_url = (
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        )
        # callback_url = "http://localhost:8000/process-stk-callback/"
        callback_url = "https://yourdomain.com/api/process-stk-callback/"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            (business_short_code + passkey + timestamp).encode()
        ).decode()
        party_a = phone_number
        party_b = business_short_code
        account_reference = "Hospital Payment"
        transaction_desc = "Payment for charge"

        stk_push_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        stk_push_payload = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": party_a,
            "PartyB": party_b,
            "PhoneNumber": party_a,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc,
        }

        print("STK push payload:", stk_push_payload)

        response = requests.post(
            process_request_url, headers=stk_push_headers, json=stk_push_payload
        )
        response_data = response.json()
        print("Response from STK push request:", response_data)

        if response_data.get("ResponseCode") == "0":
            transaction = PaymentTransaction.objects.create(
                patient=patient,
                merchant_request_id=response_data["MerchantRequestID"],
                checkout_request_id=response_data["CheckoutRequestID"],
                result_code=response_data["ResponseCode"],
                result_desc=response_data["ResponseDescription"],
                amount=amount,
                transaction_id="",
                user_phone_number=phone_number,
            )
            serializer = PaymentTransactionSerializer(transaction)
            return Response(
                {
                    "message": "STK Push initiated successfully",
                    "transaction": serializer.data,
                }
            )
        else:
            return Response(
                {
                    "error": response_data.get(
                        "errorMessage", "STK Push initiation failed"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        print("Error:", str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_stk_callback(request):
    try:
        stk_callback_response = json.loads(request.body)
        merchant_request_id = stk_callback_response["Body"]["stkCallback"][
            "MerchantRequestID"
        ]
        checkout_request_id = stk_callback_response["Body"]["stkCallback"][
            "CheckoutRequestID"
        ]
        result_code = stk_callback_response["Body"]["stkCallback"]["ResultCode"]
        result_desc = stk_callback_response["Body"]["stkCallback"]["ResultDesc"]

        transaction = PaymentTransaction.objects.get(
            checkout_request_id=checkout_request_id
        )
        transaction.result_code = result_code
        transaction.result_desc = result_desc

        if result_code == 0:
            transaction.amount = stk_callback_response["Body"]["stkCallback"][
                "CallbackMetadata"
            ]["Item"][0]["Value"]
            transaction.transaction_id = stk_callback_response["Body"]["stkCallback"][
                "CallbackMetadata"
            ]["Item"][1]["Value"]
            transaction.user_phone_number = stk_callback_response["Body"][
                "stkCallback"
            ]["CallbackMetadata"]["Item"][4]["Value"]
            transaction.save()
            serializer = PaymentTransactionSerializer(transaction)
            return Response(
                {
                    "message": "STK Callback processed successfully",
                    "transaction": serializer.data,
                }
            )
        else:
            transaction.save()
            return Response(
                {"message": result_desc}, status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_payment_status(request, transaction_id):
    try:
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
        if transaction:
            serializer = PaymentTransactionSerializer(transaction)
            return Response({"status": "success", "transaction": serializer.data})
        else:
            return Response(
                {"status": "failed", "message": "Transaction not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def appointments_per_day_data(request):
    if request.method == "GET":
        # Aggregate appointments count per day
        appointments_data = Appointment.objects.values(
            "appointment_date__date"
        ).annotate(total_appointments=Count("id"))

        # Prepare response data
        response_data = {
            "appointments_per_day": list(appointments_data),
        }

        return JsonResponse(response_data, safe=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_total_amount_paid(request):
    if request.user.role not in ["receptionist", "admin"]:
        return Response(
            {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )

    total_amount = PaymentTransaction.objects.aggregate(total=Sum("amount"))["total"]

    if total_amount is None:
        total_amount = 0.00

    return Response({"total_amount_paid": total_amount})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_patient_medical_record(request, patient_id):
    try:
        patient = Patient.objects.get(id=patient_id)
        medical_records = MedicalRecord.objects.filter(patient=patient)
        if medical_records.exists():
            serializer = MedicalRecordSerializer(medical_records, many=True)
            return Response({"status": "success", "medical_records": serializer.data})
        else:
            return Response(
                {
                    "status": "failed",
                    "message": "Medical records not found for this patient.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
    except Patient.DoesNotExist:
        return Response(
            {"status": "failed", "message": "Patient not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_patient_medical_records_with_prescriptions(request, patient_id):
    try:
        patient = Patient.objects.get(id=patient_id)
        medical_records = MedicalRecord.objects.filter(patient=patient)
        serializer = MedicalRecordWithPrescriptionsSerializer(
            medical_records, many=True
        )
        return Response({"status": "success", "medical_records": serializer.data})
    except Patient.DoesNotExist:
        return Response(
            {"status": "failed", "message": "Patient not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
