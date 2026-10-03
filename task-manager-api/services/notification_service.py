import logging
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Sends e-mail notifications through an injected SMTP factory. Disabled while no SMTP host is configured."""

    def __init__(self, settings, smtp_factory):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.sender = settings.SMTP_SENDER
        self.smtp_factory = smtp_factory

    @property
    def enabled(self):
        return bool(self.host)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info('E-mail notification skipped: SMTP is not configured')
            return False

        message = EmailMessage()
        message['From'] = self.sender
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)
        try:
            with self.smtp_factory(self.host, self.port) as server:
                server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.send_message(message)
        except OSError:
            logger.exception('Failed to send e-mail notification')
            return False
        logger.info('E-mail notification sent')
        return True

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f'Prioridade: {task.priority}\nStatus: {task.status}'
        )
        return self.send_email(user.email, subject, body)
