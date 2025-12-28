class PaymentError(Exception):
    pass


class OrderNotFoundError(PaymentError):
    pass


class UnknownOrderTypeError(PaymentError):
    pass


class PaymentGatewayError(PaymentError):
    pass
