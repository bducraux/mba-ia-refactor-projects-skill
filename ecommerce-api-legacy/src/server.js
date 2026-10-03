// Composition root: config → db → models → services → controllers → app → listen.
const config = require('./config');
const { createLogger } = require('./utils/logger');
const passwords = require('./utils/password');
const { createDatabase } = require('./database');
const { initSchema, seed } = require('./database/schema');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const PaymentGateway = require('./services/paymentGateway');
const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');
const UserService = require('./services/userService');
const buildCheckoutController = require('./controllers/checkoutController');
const buildReportController = require('./controllers/reportController');
const buildUserController = require('./controllers/userController');
const buildRequireAdmin = require('./middlewares/requireAdmin');
const buildApp = require('./app');

const logger = createLogger(config.logLevel);

async function main() {
    const db = await createDatabase(config.dbPath);
    await initSchema(db);
    await seed(db, passwords);

    const models = {
        users: new UserModel(db),
        courses: new CourseModel(db),
        enrollments: new EnrollmentModel(db),
        payments: new PaymentModel(db),
        auditLogs: new AuditLogModel(db),
    };
    const paymentGateway = new PaymentGateway({ apiKey: config.paymentGatewayKey, logger });

    const services = {
        checkout: new CheckoutService({ db, ...models, paymentGateway, passwords }),
        report: new ReportService(models),
        user: new UserService({ db, ...models }),
    };

    const controllers = {
        checkout: buildCheckoutController({ checkoutService: services.checkout }),
        report: buildReportController({ reportService: services.report }),
        user: buildUserController({ userService: services.user }),
    };

    if (!config.adminToken) logger.info('ADMIN_TOKEN não configurado: endpoints administrativos desabilitados (403).');

    const app = buildApp({ controllers, requireAdmin: buildRequireAdmin(config), logger });
    app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}...`));
}

main().catch((err) => {
    logger.error('Falha ao iniciar a aplicação:', err);
    process.exit(1);
});
