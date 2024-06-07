from django.urls import path
from .views import (
    create_patient,
    add_medical_record,
    create_admin,
    create_user,
    user_login,
    list_patients,
    get_patient,
    book_appointment_for_patient,
    doctor_appointments,
    create_prescription,
    # patient_appointments,
)

urlpatterns = [
    # Auth Routes
    path("user/create-admin/", create_admin, name="create_admin"),
    path("user/create-user/", create_user, name="create_user"),
    path("user/login/", user_login, name="user_login"),
    # Reception routes
    path("add_patient/", create_patient, name="create_patient"),
    path("patients/", list_patients, name="list_patients"),
    path("patients/<int:patient_id>/", get_patient, name="get_patient"),
    # path("book-appointment/", book_appointment, name="book_appointment"),
    path(
        "book-appointment/<int:patient_id>/",
        book_appointment_for_patient,
        name="book_appointment_for_patient",
    ),
    # DOctors Routes
    path("doctor/appointments/", doctor_appointments, name="doctor_appointments"),
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
    # path(
    #     "patients/<int:patient_id>/appointments/",
    #     patient_appointments,
    #     name="patient-appointments",
    # ),
    # Pharmacist routes
    # path("charges/", charge_patient, name="charge_patient"),
]
