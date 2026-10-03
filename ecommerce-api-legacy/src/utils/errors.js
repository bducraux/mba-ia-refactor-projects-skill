const { MESSAGES } = require('./constants');

// Domain errors carry the original HTTP status and plain-text message of the API.
class AppError extends Error {
    constructor(message, status = 500) {
        super(message);
        this.name = this.constructor.name;
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor(message = MESSAGES.BAD_REQUEST) { super(message, 400); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

class PaymentDeclinedError extends AppError {
    constructor(message = MESSAGES.PAYMENT_DENIED) { super(message, 400); }
}

class ForbiddenError extends AppError {
    constructor(message = MESSAGES.FORBIDDEN) { super(message, 403); }
}

module.exports = { AppError, ValidationError, NotFoundError, PaymentDeclinedError, ForbiddenError };
