const LEVELS = { debug: 10, info: 20, error: 30 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] || LEVELS.info;
    const write = (name, stream) => (...args) => {
        if (LEVELS[name] >= threshold) stream(`[${name}]`, ...args);
    };
    return {
        debug: write('debug', console.log),
        info: write('info', console.log),
        error: write('error', console.error),
    };
}

module.exports = { createLogger };
