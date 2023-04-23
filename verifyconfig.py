from config import API_BASE_URL, SYNC_CHECK_BLOCK_THRESHOLD, BLOCK_PRODUCER_USERNAME, WALLET_MNEMONIC, \
    WALLET_SECOND_MNEMONIC, VOTE_CAP, MESSAGE, MESSAGE_INTERVAL_SECONDS, MESSAGE_LIMIT_PER_VOTER


def verify_values():
    if API_BASE_URL == "" or API_BASE_URL is None:
        raise Exception(
            "Invalid API_BASE_URL, valid example: \"http://localhost:<port>/api\""
        )
    if not API_BASE_URL.endswith("/api"):
        raise Exception(
            "Invalid API_BASE_URL, needs to end in '/api'"
        )
    if SYNC_CHECK_BLOCK_THRESHOLD < 1:
        raise Exception(
            "Invalid SYNC_CHECK_BLOCK_THRESHOLD, too low"
        )
    if BLOCK_PRODUCER_USERNAME == "" or BLOCK_PRODUCER_USERNAME is None:
        raise Exception(
            "Invalid BLOCK_PRODUCER_USERNAME, may not be empty or None"
        )
    if WALLET_MNEMONIC == "" or WALLET_MNEMONIC is None:
        raise Exception(
            "Invalid WALLET_MNEMONIC, may not be empty or None"
        )
    if WALLET_SECOND_MNEMONIC == "":
        raise Exception(
            "Invalid WALLET_SECOND_MNEMONIC, use None instead of empty str"
        )
    if VOTE_CAP < 1:
        raise Exception(
            "Invalid VOTE_CAP, too low"
        )
    if MESSAGE == "" or MESSAGE is None:
        raise Exception(
            "Invalid MESSAGE, may not be empty or None"
        )
    if MESSAGE_INTERVAL_SECONDS < 3600:
        raise Exception(
            "Invalid MESSAGE_INTERVAL_SECONDS, 3600s (1h) is the smallest allowed interval"
        )
    if MESSAGE_LIMIT_PER_VOTER == 0 or MESSAGE_LIMIT_PER_VOTER < -1:
        raise Exception(
            "Invalid MESSAGE_LIMIT_PER_VOTER, use -1 to disable limit"
        )
