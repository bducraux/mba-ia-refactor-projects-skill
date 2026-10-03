import logging

from src.utils.constants import STATUS_APROVADO, STATUS_CANCELADO

logger = logging.getLogger(__name__)


class NotificacaoService:
    """Ponto único dos efeitos colaterais de notificação (hoje apenas registrados em log)."""

    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Email enviado: pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("SMS enviado: pedido %s recebido", pedido_id)
        logger.info("Push enviado: novo pedido %s", pedido_id)

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == STATUS_APROVADO:
            logger.info("Pedido %s aprovado: preparar envio", pedido_id)
        elif novo_status == STATUS_CANCELADO:
            logger.info("Pedido %s cancelado: devolver estoque", pedido_id)
