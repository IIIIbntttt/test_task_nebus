from payments.shared.enums import Currency, PaymentStatus


def test_currency_values() -> None:
    assert {item.value for item in Currency} == {"RUB", "USD", "EUR"}


def test_payment_status_values() -> None:
    assert {item.value for item in PaymentStatus} == {"pending", "succeeded", "failed"}
