const { AppError } = require('../utils/errors');
const { MESSAGES } = require('../utils/constants');

// Single error → HTTP mapping. Errors keep the original plain-text bodies of the API.
function buildErrorHandler({ logger }) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (err instanceof AppError) return res.status(err.status).send(err.message);

        // Malformed JSON and other client errors raised by express.json().
        if (err.status >= 400 && err.status < 500) return res.status(err.status).send(MESSAGES.BAD_REQUEST);

        logger.error(`${req.method} ${req.originalUrl} falhou:`, err);
        res.status(500).send(MESSAGES.INTERNAL_ERROR);
    };
}

module.exports = buildErrorHandler;
