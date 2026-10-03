const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../utils/constants');

// Simulated gateway: same approval rule as the original API, without logging card data or keys.
class PaymentGateway {
    constructor({ apiKey, logger }) {
        this.apiKey = apiKey;
        this.logger = logger;
    }

    async charge({ cardNumber, amount }) {
        const status = cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        this.logger.info(`Pagamento de ${amount} no cartão final ${cardNumber.slice(-4)}: ${status}`);
        return status;
    }
}

module.exports = PaymentGateway;
