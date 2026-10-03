// Forwards rejected promises from async controllers to the error middleware.
module.exports = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
