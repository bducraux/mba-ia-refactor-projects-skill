const { PAYMENT_STATUS, MESSAGES } = require('../utils/constants');
const { NotFoundError, PaymentDeclinedError } = require('../utils/errors');

class CheckoutService {
    constructor({ db, users, courses, enrollments, payments, auditLogs, paymentGateway, passwords }) {
        Object.assign(this, { db, users, courses, enrollments, payments, auditLogs, paymentGateway, passwords });
    }

    async checkout({ name, email, password, courseId, cardNumber }) {
        const course = await this.courses.findActiveById(courseId);
        if (!course) throw new NotFoundError(MESSAGES.COURSE_NOT_FOUND);

        const status = await this.paymentGateway.charge({ cardNumber, amount: course.price });
        if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeclinedError();

        const passwordHash = await this.passwords.hashPassword(password || this.passwords.randomPassword());

        return this.db.transaction(async () => {
            const existing = await this.users.findIdByEmail(email);
            const userId = existing ? existing.id : await this.users.create({ name, email, passwordHash });
            const enrollmentId = await this.enrollments.create({ userId, courseId });
            await this.payments.create({ enrollmentId, amount: course.price, status });
            await this.auditLogs.create(`Checkout curso ${courseId} por ${userId}`);
            return { enrollmentId };
        });
    }
}

module.exports = CheckoutService;
