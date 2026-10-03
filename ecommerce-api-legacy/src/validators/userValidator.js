const { ValidationError } = require('../utils/errors');

function validateUserId(rawId) {
    const userId = Number(rawId);
    if (!/^\d+$/.test(String(rawId)) || userId <= 0) throw new ValidationError();
    return userId;
}

module.exports = { validateUserId };
