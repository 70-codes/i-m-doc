from django.urls import path
from .views import (
    create_patient,
    add_medical_record,
    create_admin,
    create_user,
    get_patient_medical_records_with_prescriptions,
    user_login,
    list_patients,
    get_patient,
    book_appointment_for_patient,
    doctor_appointments,
    create_prescription,
    # patient_appointments,
    get_user_name,
    get_prescriptions,
    initiate_stk_push,
    process_stk_callback,
    get_patient_full_name,
    appointments_per_day_data,
    get_total_amount_paid,
    get_patient_medical_record,
)

urlpatterns = [
    # Auth Routes
    path(
        "user/create-admin/",
        create_admin,
        name="create_admin",
    ),
    path(
        "user/create-user/",
        create_user,
        name="create_user",
    ),
    path(
        "user/login/",
        user_login,
        name="user_login",
    ),
    # Reception routes
    path(
        "add_patient/",
        create_patient,
        name="create_patient",
    ),
    path(
        "patients/",
        list_patients,
        name="list_patients",
    ),
    path(
        "patients/<int:patient_id>/",
        get_patient,
        name="get_patient",
    ),
    # path("book-appointment/",
    # book_appointment, name="book_appointment"),
    path(
        "book-appointment/<int:patient_id>/",
        book_appointment_for_patient,
        name="book_appointment_for_patient",
    ),
    # DOctors Routes
    path(
        "doctor/appointments/",
        doctor_appointments,
        name="doctor_appointments",
    ),
    path(
        "patient-full-name/<int:patient_id>/",
        get_patient_full_name,
        name="get_patient_full_name",
    ),
    path(
        "add-medical-record/<int:patient_id>/",
        add_medical_record,
        name="add_medical_record",
    ),
    path(
        "create-prescription/<int:medical_record_id>/",
        create_prescription,
        name="create_prescription",
    ),
    path(
        "api/user/<int:user_id>/",
        get_user_name,
        name="get_user_name",
    ),
    # Pharmacist routes
    path(
        "get-prescriptions/",
        get_prescriptions,
    ),
    # charge patient
    path(
        "stkpush/<int:patient_id>/",
        initiate_stk_push,
        name="initiate_stk_push",
    ),
    path(
        "process-stk-callback/",
        process_stk_callback,
        name="process_stk_callback",
    ),
    # Admin Dashboard Routes
    path(
        "appointments-per-day-data/",
        appointments_per_day_data,
        name="appointments_per_day_data",
    ),
    path(
        "api/total-amount-paid/",
        get_total_amount_paid,
        name="total-amount-paid",
    ),
    path(
        "patient-medical-record/<int:patient_id>/",
        get_patient_medical_record,
        name="get_patient_medical_record",
    ),
    path(
        "patient-medical-records-with-prescriptions/<int:patient_id>/",
        get_patient_medical_records_with_prescriptions,
        name="patient-medical-records-with-prescriptions",
    ),
]
