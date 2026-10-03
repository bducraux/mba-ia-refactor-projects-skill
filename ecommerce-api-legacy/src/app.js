const express = require('express');
const buildRoutes = require('./routes');
const buildErrorHandler = require('./middlewares/errorHandler');

// Builds the Express app from already-wired controllers (no listen here).
function buildApp({ controllers, requireAdmin, logger }) {
    const app = express();
    app.use(express.json());
    app.use(buildRoutes({ controllers, requireAdmin }));
    app.use(buildErrorHandler({ logger }));
    return app;
}

module.exports = buildApp;
