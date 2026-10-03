const { validateCheckout } = require('../validators/checkoutValidator');
const { MESSAGES } = require('../utils/constants');

function buildCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            const input = validateCheckout(req.body);
            const { enrollmentId } = await checkoutService.checkout(input);
            res.status(200).json({ msg: MESSAGES.CHECKOUT_SUCCESS, enrollment_id: enrollmentId });
        },
    };
}

module.exports = buildCheckoutController;
