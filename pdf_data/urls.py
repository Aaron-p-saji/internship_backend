from django.urls import path
from .views import (
    getPdfUserData,
    ListUserPDFsView,
    RetrievePDFView,
    sendCertificate,
    sendMail,
    ThumbnailView,
    UploadPDFView,
)

urlpatterns = [
    path("retrieve/", RetrievePDFView.as_view(), name="retrieve-pdf"),
    path("pdfs/list/", ListUserPDFsView.as_view(), name="list_pdfs"),
    path("pdfs/thumbnail/<filename>/", ThumbnailView.as_view(), name="thumbnail"),
    path("upload/", UploadPDFView.as_view(), name="upload-pdf"),
    path("sendemail/", sendMail, name="send-email"),
    path("sendcertificate/", sendCertificate, name="send-certificate"),
    path("get_pdfData/", getPdfUserData, name="getPdfData"),
]
