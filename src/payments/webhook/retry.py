def exponential_backoff_delay_seconds(retry_attempt: int) -> float:
    return float(2**retry_attempt)
