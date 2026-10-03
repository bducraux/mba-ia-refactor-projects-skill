const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LENGTH = 64;

async function hashPassword(raw) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const derived = await scrypt(raw, salt, KEY_LENGTH);
    return `${salt}:${derived.toString('hex')}`;
}

// Used when a buyer does not send a password: the account gets an unguessable one.
function randomPassword() {
    return crypto.randomBytes(24).toString('base64url');
}

module.exports = { hashPassword, randomPassword };
