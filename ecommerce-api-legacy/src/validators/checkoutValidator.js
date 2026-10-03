const { ValidationError } = require('../utils/errors');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const DIGITS_PATTERN = /^\d+$/;

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

// Request fields keep their original names (usr, eml, pwd, c_id, card); output uses domain names.
function validateCheckout(body) {
    const { usr, eml, pwd, c_id: rawCourseId, card } = body || {};
    if (!usr || !eml || !rawCourseId || !card) throw new ValidationError();

    const courseId = Number(rawCourseId);
    const valid = isNonEmptyString(usr)
        && isNonEmptyString(eml) && EMAIL_PATTERN.test(eml)
        && Number.isInteger(courseId) && courseId > 0
        && typeof card === 'string' && DIGITS_PATTERN.test(card)
        && (pwd === undefined || pwd === null || typeof pwd === 'string');
    if (!valid) throw new ValidationError();

    return { name: usr.trim(), email: eml.trim(), password: pwd || null, courseId, cardNumber: card };
}

module.exports = { validateCheckout };
