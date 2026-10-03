// Single source of runtime settings. Defaults are safe for local development only.
module.exports = Object.freeze({
    port: Number(process.env.PORT || 3000),
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    // Admin endpoints are disabled (403) while no token is configured.
    adminToken: process.env.ADMIN_TOKEN || '',
    logLevel: process.env.LOG_LEVEL || 'info',
});
