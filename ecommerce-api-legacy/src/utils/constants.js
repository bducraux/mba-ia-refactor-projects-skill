const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Fake gateway rule kept from the original API: cards starting with "4" are approved.
const APPROVED_CARD_PREFIX = '4';

const MESSAGES = Object.freeze({
    CHECKOUT_SUCCESS: 'Sucesso',
    BAD_REQUEST: 'Bad Request',
    COURSE_NOT_FOUND: 'Curso não encontrado',
    PAYMENT_DENIED: 'Pagamento recusado',
    FORBIDDEN: 'Acesso negado',
    USER_DELETED: 'Usuário deletado, junto com suas matrículas e pagamentos.',
    INTERNAL_ERROR: 'Erro interno',
});

const UNKNOWN_STUDENT = 'Unknown';

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX, MESSAGES, UNKNOWN_STUDENT };
