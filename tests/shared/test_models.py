from payments.shared.models import OutboxModel, PaymentModel


def test_payment_table_name() -> None:
    assert PaymentModel.__tablename__ == "payments"


def test_outbox_table_name() -> None:
    assert OutboxModel.__tablename__ == "outbox"


def test_payment_idempotency_key_is_unique() -> None:
    unique_columns = {
        column.name
        for constraint in PaymentModel.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
        for column in constraint.columns
    }
    assert "idempotency_key" in unique_columns
