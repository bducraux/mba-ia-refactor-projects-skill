const crypto = require('crypto');
const { ForbiddenError } = require('../utils/errors');

function tokensMatch(received, expected) {
    const a = Buffer.from(received);
    const b = Buffer.from(expected);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
}

// Requires the X-Admin-Token header to match config.adminToken; disabled when no token is configured.
function buildRequireAdmin({ adminToken }) {
    return (req, res, next) => {
        const received = req.get('X-Admin-Token') || '';
        if (!adminToken || !tokensMatch(received, adminToken)) return next(new ForbiddenError());
        next();
    };
}

module.exports = buildRequireAdmin;
