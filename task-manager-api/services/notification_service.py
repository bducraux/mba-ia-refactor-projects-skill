import logging
import smtplib

logger = logging.getLogger(__name__)


class NotificationService:
    """Sends e-mail notifications; SMTP settings are injected from config."""

    def __init__(self, host, port, user, password, sender, smtp_factory=smtplib.SMTP):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.sender = sender or user
        self.smtp_factory = smtp_factory

    @property
    def enabled(self):
        return bool(self.host)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info('SMTP not configured; skipping e-mail "%s"', subject)
            return False
        try:
            with self.smtp_factory(self.host, self.port) as server:
                server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.sendmail(self.sender, to, f'Subject: {subject}\n\n{body}')
            logger.info('E-mail sent: "%s"', subject)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('Failed to send e-mail "%s"', subject)
            return False

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f'Prioridade: {task.priority}\nStatus: {task.status}')
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f'Task atrasada: {task.title}'
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)
