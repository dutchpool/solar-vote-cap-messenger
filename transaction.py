from datetime import datetime
from typing import Optional, Dict

from solar_client import SolarClient
from solar_client.exceptions import SolarHTTPException
from solar_crypto.configuration.network import set_custom_network
from solar_crypto.identity.address import address_from_passphrase
from solar_crypto.transactions.builder.transfer import Transfer

from config import TRANSACTION_NETWORK, API_BASE_URL


class Payment(object):
    def __init__(self, recipient: str, amount: int):
        self.recipient: str = recipient
        self.amount: int = amount


def build_network():
    e = TRANSACTION_NETWORK["epoch"].split(",")
    version = TRANSACTION_NETWORK["version"]
    wif = TRANSACTION_NETWORK["wif"]
    t = [int(i) for i in e]
    epoch = datetime(t[0], t[1], t[2], t[3], t[4], t[5])
    set_custom_network(epoch, version, wif)


client = SolarClient(API_BASE_URL)
build_network()

cached_dynamic_fees_config: Optional[Dict] = None


def get_nonce(address: str) -> int:
    try:
        n = client.wallets.get(address)
    except SolarHTTPException as e:
        raise Exception(e, "failure while getting nonce")

    return int(n["data"]["nonce"])


def build_transfer_transaction(
        payments: [Payment],
        memo: Optional[str],
        fee: int,
        sig: str,
        second_sig: Optional[str],
        nonce: int
) -> Transfer:
    if fee <= 0:
        raise Exception("fee is too low")

    transaction = Transfer(
        memo=memo,
        fee=fee
    )

    for payment in payments:
        if payment.amount <= 0:
            raise Exception(f"transfer amount to {payment.recipient} is too low")
        transaction.add_transfer(
            recipient_id=payment.recipient,
            amount=payment.amount,
        )

    transaction.set_nonce(nonce)
    transaction.sign(sig)

    if second_sig is not None:
        transaction.second_sign(second_sig)

    return transaction


def broadcast(tx: Transfer) -> (bool, str):
    try:
        transaction = client.transactions.create([tx.to_dict()])
    except SolarHTTPException as e:
        raise Exception(e, "failure while broadcasting transaction")
    success = len(transaction["data"]["accept"]) != 0
    error = next(iter(transaction["errors"].values()), None) if "errors" in transaction else None
    error_message = "" if error is None else error["message"]
    return success, error_message


def get_cached_dynamic_fees_config() -> Dict:
    global cached_dynamic_fees_config
    if cached_dynamic_fees_config is None:
        try:
            cached_dynamic_fees_config = client.node.configuration()["data"]["pool"]["dynamicFees"]
        except Exception as e:
            raise Exception(e, "failure while getting dynamic fees config")
    return cached_dynamic_fees_config


def get_dynamic_fee(payment_count: int, memo: Optional[str], is_second_sig_present: bool) -> int:
    dynamic_fees_config = get_cached_dynamic_fees_config()
    transfer_addon_bytes = dynamic_fees_config["addonBytes"]["transfer"]
    transfer_bytes = 125
    payment_bytes = 29 * payment_count
    memo_bytes = 0 if memo is None else len(memo.encode())
    second_sig_bytes = 64 if is_second_sig_present else 0
    tx_bytes = transfer_bytes + payment_bytes + memo_bytes + second_sig_bytes
    fee_multiplier = dynamic_fees_config["minFeePool"]
    return int((transfer_addon_bytes + (round(tx_bytes / 2) + 1)) * fee_multiplier)


def transfer(
        payments: [Payment],
        memo: Optional[str],
        fee: Optional[int],
        sig: str,
        second_sig: Optional[str],
        nonce: Optional[int]
):
    if fee is None:
        fee = get_dynamic_fee(len(payments), memo, second_sig is not None)
    if nonce is None:
        nonce = get_nonce(address_from_passphrase(sig)) + 1
    tx = build_transfer_transaction(payments, memo, fee, sig, second_sig, nonce)
    success, error_message = broadcast(tx)
    if not success:
        raise Exception(error_message)
