class UserService {
    constructor({ db, users, enrollments, payments }) {
        Object.assign(this, { db, users, enrollments, payments });
    }

    // Removes the user with its enrollments and payments atomically (no orphan rows).
    deleteUser(userId) {
        return this.db.transaction(async () => {
            await this.payments.deleteByUserId(userId);
            await this.enrollments.deleteByUserId(userId);
            await this.users.deleteById(userId);
        });
    }
}

module.exports = UserService;
