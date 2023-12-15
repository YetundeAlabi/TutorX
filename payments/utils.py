from django.conf import settings
from django.core.mail import EmailMultiAlternatives


class EmailSender:

    @classmethod
    def _send_email(cls, subject, mail_content, recipient, from_email):
        msg = EmailMultiAlternatives(
            subject, mail_content, from_email, [recipient])
        msg.attach_alternative(mail_content, "text/html")
        msg.send()

    @classmethod
    def teacher_payment_mail(cls, recipient, mail_body):
        subject = "Your Pay Slip Has Arrived"
        from_email = settings.EMAIL_HOST_USER
        return cls._send_email(subject=subject, mail_content=mail_body, recipient=recipient,
                               from_email=from_email)
