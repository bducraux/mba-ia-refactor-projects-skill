const { validateUserId } = require('../validators/userValidator');
const { MESSAGES } = require('../utils/constants');

function buildUserController({ userService }) {
    return {
        async remove(req, res) {
            const userId = validateUserId(req.params.id);
            await userService.deleteUser(userId);
            res.send(MESSAGES.USER_DELETED);
        },
    };
}

module.exports = buildUserController;
