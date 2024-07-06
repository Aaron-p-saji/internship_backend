import os
import uuid
import psutil
import threading
from datetime import date
from interns.serializers import InternSerializer
from .models import UserPDF
from hr_backend import settings
from django.conf import settings
from interns.models import Interns
from django.http import FileResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from django.core.mail import EmailMessage, EmailMultiAlternatives
from rest_framework.response import Response
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from hr_backend.settings import EMAIL_HOST_USER
from pdf_data.utils import generate_pdf_thumbnail
from rest_framework.parsers import MultiPartParser
from .serializers import PDFUploadSerializer, UserPDFSerializer
from rest_framework.decorators import api_view, permission_classes


class RetrievePDFView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        filename = request.GET.get("filename")
        if filename:
            user_pdf = get_object_or_404(UserPDF, filename=filename)
            if user_pdf:
                serializer = UserPDFSerializer(user_pdf)
                filepath = os.path.join(
                    settings.CERTIFICATES_DIR, f"{user_pdf.filename}.pdf"
                )
                response = FileResponse(
                    open(filepath, "rb"), as_attachment=True, filename=user_pdf.filename
                )
                response["Content-Type"] = "application/pdf"
                return response
            else:
                return JsonResponse({"message": "File not found"}, status=404)
        else:
            return JsonResponse(
                {"message": "filename parameter is required"}, status=400
            )


class UploadPDFView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        serializer = PDFUploadSerializer(data=request.data)
        if serializer.is_valid():
            file_obj = serializer.validated_data["file"]
            user_id = serializer.validated_data["user_id"]

            # Generate a UUID4 filename
            filename = f"{uuid.uuid4()}.pdf"
            filepath = os.path.join(settings.CERTIFICATES_DIR, filename)

            # Save the file to the server
            with open(filepath, "wb+") as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            # Save the file path and user_id to the database
            user_pdf = UserPDF.objects.create(
                user_id=user_id, filename=filename.split(".")[0]
            )

            return Response(
                {"message": "File uploaded successfully", "filename": filename},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListUserPDFsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if "user_id" in request.query_params:
            user_pdfs = UserPDF.objects.filter(
                user_id=request.query_params.get("user_id")
            )
            if not user_pdfs.exists():
                return Response(
                    {"detail": "No PDFs found for this user."},
                    status=status.HTTP_200_OK,
                )
            serializer = UserPDFSerializer(
                user_pdfs, many=True, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "User_id not passed"}, status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, *args, **kwargs):
        pdf_id = request.data.get("pdf_id")
        if not pdf_id:
            return Response(
                {"message": "Missing parameter pdf_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pdf = UserPDF.objects.get(filename=pdf_id)
        except UserPDF.DoesNotExist:
            return Response(
                {"message": "PDF does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        filepath = os.path.join(settings.CERTIFICATES_DIR, f"{pdf_id}.pdf")

        # Check if the file exists
        if not os.path.isfile(filepath):
            return Response(
                {"message": "File does not exist on server"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if the file is being used
        if self.is_file_in_use(filepath):
            return Response(
                {"message": "File is currently in use and cannot be deleted"},
                status=status.HTTP_423_LOCKED,  # 423 Locked
            )

        try:
            os.remove(filepath)
            pdf.delete()
            return Response(
                {"message": "Requested PDF deleted"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": f"Error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def is_file_in_use(self, filepath):
        for proc in psutil.process_iter(["open_files"]):
            if any(map(lambda x: x.path == filepath, proc.info["open_files"] or [])):
                return True
        return False


class ThumbnailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, filename):
        if not filename.endswith(".png"):
            return Response(
                {"detail": "Invalid filename extension. Must end with .png."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        filename = str(filename).split(".")[0]
        try:
            user_pdf = UserPDF.objects.get(filename=filename)
        except UserPDF.DoesNotExist:
            raise Http404("PDF not found.")

        pdf_path = os.path.join(settings.CERTIFICATES_DIR, f"{user_pdf.filename}.pdf")
        thumbnail_data = generate_pdf_thumbnail(pdf_path)

        if not thumbnail_data:
            return Response(
                {"detail": "Thumbnail generation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(thumbnail_data, content_type="image/png")
        response["Content-Disposition"] = f"inline; filename={filename}_thumbnail.png"
        return response


def send_email_in_background(recipient, subject, mail_body, files):
    try:
        mail = EmailMessage(subject, mail_body, settings.EMAIL_HOST_USER, [recipient])
        if files:
            for file in files:
                mail.attach(file.name, file.read(), file.content_type)
            mail.send()
            print(f"Mail sent successfully to {recipient}")
        else:
            mail.send()
    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def sendMail(request):
    recipient = request.data.get("recipient")
    subject = request.data.get("subject")
    mail_body = request.data.get("mail")
    files = request.FILES.getlist("files")

    if recipient and subject and mail_body:
        threading.Thread(
            target=send_email_in_background, args=(recipient, subject, mail_body, files)
        ).start()
        return JsonResponse(
            {"response": f"Started sending email to {recipient}"}, status=200
        )
    else:
        return JsonResponse(
            {"response": "Please enter required parameters"}, status=400
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def sendCertificate(request):
    filename = request.GET.get("filename")
    print(filename)

    if filename:
        try:
            pdf = UserPDF.objects.get(filename=filename)
        except UserPDF.DoesNotExist:
            return JsonResponse(
                {"response": f"PDF not found", "filename": filename}, status=404
            )
    else:
        return JsonResponse(
            {"response": "Incoming Data Error", "filename": filename}, status=500
        )

    pdf_file = os.path.join(settings.CERTIFICATES_DIR, f"{pdf.filename}.pdf")

    try:
        user = Interns.objects.get(intern_code=pdf.user_id)
    except Interns.DoesNotExist:
        return JsonResponse(
            {"response": f"Internal Server Error ${pdf_file}"}, status=500
        )

    recipient = user.email
    send_filename = f"{user.full_name}_Cerificate"
    subject = "Certificate"
    link = f"http://localhost:3000/viewer/file/{pdf.user_id}.pdf"

    mail_body = f"""
    <p>This is your certificate. You can also view this in the browser using the following link:</p>
    <a href="{link}">View Certificate</a>
    """

    if recipient and subject and mail_body:
        mail = EmailMultiAlternatives(
            subject, "", settings.EMAIL_HOST_USER, [recipient]
        )
        mail.attach_alternative(mail_body, "text/html")
        mail.attach(
            f"certificate_{send_filename}_{date.today()}",
            open(pdf_file, "rb").read(),
            "application/pdf",
        )
        threading.Thread(target=mail.send).start()
        return JsonResponse(
            {"response": f"Started sending email to {recipient}"}, status=200
        )
    else:
        return JsonResponse(
            {"response": "Please enter required parameters"}, status=400
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def getPdfUserData(request):
    filename = request.GET.get("filename")
    print(f"Filename received: {filename}")

    if filename:
        try:
            pdf = UserPDF.objects.get(filename=filename)
            print(f"PDF found: {pdf}")
            print(f"User found: {pdf.user_id}")

            try:
                user = Interns.objects.get(pk=pdf.user_id)
                print(f"Intern found: {user}")

                serializer = InternSerializer(user)
                return JsonResponse(serializer.data, status=200)

            except Interns.DoesNotExist:
                return JsonResponse(
                    {"response": f"Intern not found for user_id: {pdf.user_id}"},
                    status=404,
                )

        except UserPDF.DoesNotExist:
            return JsonResponse(
                {"response": f"PDF not found", "filename": filename}, status=200
            )
    else:
        return JsonResponse(
            {"response": "Incoming Data Error", "filename": filename}, status=400
        )
