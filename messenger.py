from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime, time
from typing import Dict, Optional

from config import SYNC_CHECK_BLOCK_THRESHOLD, MESSAGE, WALLET_MNEMONIC, WALLET_SECOND_MNEMONIC, VOTE_CAP, \
    MESSAGE_INTERVAL_SECONDS, BLOCK_PRODUCER_USERNAME, MESSAGE_LIMIT_PER_VOTER, EXCLUDE_VOTERS
from core_api import get_node_status, Peer, get_peers, Wallet, get_voters, VotingFor
from data import get_last_activation_timestamp, set_last_activation_timestamp, get_activations, set_activations
from error import handle_error
from transaction import transfer, Payment
from utils import from_atomic_formatted, time_delta_formatted

ALLOW_NEW_ACTIVE_PERCENTAGE = 0.05
ALLOW_NEW_ACTIVE_SECONDS = 2 * 60 * 60
TIME_FORMAT = "%H:%M"


def parse_set_time(time_str: str) -> time:
    try:
        return datetime.strptime(time_str, TIME_FORMAT).time()
    except ValueError:
        raise ArgumentTypeError(f"Invalid time format '{time_str}'. Use format 'HH:MM'.")


parser = ArgumentParser(description="Send a message to voters over your vote cap")
parser.add_argument(
    "-t", "--test",
    action="store_true",
    help="Use this flag to run the script in test mode, no transactions will be made",
    required=False
)
parser.add_argument(
    "-d", "--dev",
    action="store_true",
    help="Use this flag to run the script in development mode, data storage behavior will be changed",
    required=False
)
parser.add_argument(
    "-st", "--settime",
    type=parse_set_time,
    help="Change the time of the interval in format 'HH:MM'",
    required=False
)
args = parser.parse_args()

now = int(datetime.now().timestamp())


def send_messages(voters_to_message: [Wallet]):
    payments = [Payment(voter.address, 1) for voter in voters_to_message]
    try:
        transfer(
            payments=payments,
            memo=MESSAGE,
            fee=None,
            sig=WALLET_MNEMONIC,
            second_sig=WALLET_SECOND_MNEMONIC,
            nonce=None
        )
    except Exception as e:
        handle_error(e, "Failed to send messages", True)


def get_voters_to_message(
        is_test: bool,
        is_dev: bool,
        is_active: bool,
        is_new_active: bool,
        voters: [Wallet]
) -> [Wallet]:
    activations = get_activations()
    voters_to_message: [Wallet] = []

    for voter in voters:
        if voter.address in EXCLUDE_VOTERS:
            continue
        if voter.address in activations:
            activation_count = activations[voter.address]
            activations[voter.address] = activation_count
            if is_active:
                if MESSAGE_LIMIT_PER_VOTER == -1 or activation_count < MESSAGE_LIMIT_PER_VOTER:
                    activations[voter.address] = activation_count + 1
                    voters_to_message.append(voter)
        else:
            if is_active or is_new_active:
                activations[voter.address] = 1
                voters_to_message.append(voter)
    if not is_test or is_dev:
        set_activations(activations)
    return voters_to_message


def find_voting_for(username: str, voting_for: [VotingFor]) -> Optional[VotingFor]:
    return next((vf for vf in voting_for if vf.username == username), None)


def get_voters_over_cap(username: str) -> [Wallet]:
    try:
        voters = get_voters(username)
        return [
            voter for voter in voters
            if (voting_for := find_voting_for(username, voter.voting_for)) is not None and voting_for.votes > VOTE_CAP
        ]
    except Exception as e:
        handle_error(e, f"Failed to get voters over cap for username {username}", True)


def is_messenger_new_active(seconds_till_activation: int) -> bool:
    # hold off on sending message to new voters when the regular interval is coming up
    return seconds_till_activation / MESSAGE_INTERVAL_SECONDS > ALLOW_NEW_ACTIVE_PERCENTAGE \
           or seconds_till_activation > ALLOW_NEW_ACTIVE_SECONDS


def is_messenger_active(last_activation: int) -> (bool, int):
    active = now - last_activation > MESSAGE_INTERVAL_SECONDS
    seconds_till_activation = 0 if last_activation == 0 else MESSAGE_INTERVAL_SECONDS - (now - last_activation)
    if active:
        set_last_activation_timestamp(now)
    return active, seconds_till_activation


def validate_peers_sync(height: int, peers: [Peer]) -> (bool, Dict[int, int]):
    height_map: Dict[int, int] = {}
    for peer in peers:
        if peer.height in height_map:
            height_map[peer.height] += 1
        else:
            height_map[peer.height] = 1
    height_map = {
        k: v for k, v in sorted(height_map.items(), key=lambda item: item[1], reverse=True)
    }
    if not height_map:
        return False, height_map
    common_height = next(iter(height_map))
    if common_height - SYNC_CHECK_BLOCK_THRESHOLD <= height <= common_height + SYNC_CHECK_BLOCK_THRESHOLD:
        return True, height_map
    else:
        return False, height_map


def verify_node_status():
    try:
        node_status = get_node_status()
        is_status_synced = node_status.synced
        block_height = node_status.now
        blocks_count = node_status.blocks_count
        if not is_status_synced:
            raise Exception(
                f"Node unavailable or out of sync [status] height:{block_height} blocks_count:{blocks_count}"
            )
        peers = get_peers()
        is_peers_synced, peers_heights = validate_peers_sync(block_height, peers)
        if not is_peers_synced:
            raise Exception(
                f"Node unavailable or out of sync [peers] height:{block_height} blocks_count:{blocks_count} peers_heights:{peers_heights}"
            )
    except Exception as e:
        handle_error(e, "Failed to verify node status", True)


def set_new_activation_time(is_test: bool, last_activation: int, new_time: time):
    if last_activation == 0:
        new_timestamp = int(
            datetime.combine(datetime.fromtimestamp(now - MESSAGE_INTERVAL_SECONDS), new_time).timestamp()
        )
    else:
        new_timestamp = int(
            datetime.combine(datetime.fromtimestamp(last_activation), new_time).timestamp()
        )
    new_time_str = new_time.strftime(TIME_FORMAT)
    if is_test:
        print(f"""Test changed activation time to {new_time_str}""")
    else:
        set_last_activation_timestamp(new_timestamp)
        print(f"""Changed activation time to {new_time_str}""")


def main():
    is_test = args.test
    is_dev = args.dev
    new_time = args.settime
    last_activation = get_last_activation_timestamp()
    if new_time is not None:
        set_new_activation_time(is_test, last_activation, new_time)
        return
    verify_node_status()
    is_active, seconds_till_activation = is_messenger_active(last_activation)
    is_new_active = is_messenger_new_active(seconds_till_activation)
    next_time_str = datetime.fromtimestamp(now + seconds_till_activation).strftime(TIME_FORMAT)
    if not is_active and not is_new_active:
        print(f"Next activation in {time_delta_formatted(seconds_till_activation)} at {next_time_str}")
        return
    voters = get_voters_over_cap(BLOCK_PRODUCER_USERNAME)
    voters_to_message = get_voters_to_message(is_test, is_dev, is_active, is_new_active, voters)
    if (not is_test or is_dev) and is_active:
        set_last_activation_timestamp(now)
    voters_to_message_count = len(voters_to_message)
    if voters_to_message_count == 0:
        if is_active:
            print(
                f"No voters over the {from_atomic_formatted(VOTE_CAP, 0)} SXP vote cap for block producer {BLOCK_PRODUCER_USERNAME}"
            )
        else:
            print(f"Next activation in {time_delta_formatted(seconds_till_activation)} at {next_time_str}")
        return
    if is_test:
        logging_messages = [
            f"""- {voter.address} {from_atomic_formatted(vf.votes, 0) if (vf := find_voting_for(BLOCK_PRODUCER_USERNAME, voter.voting_for)) is not None else ""} SXP"""
            for voter in voters_to_message
        ]
        print(
            f"Test message to {voters_to_message_count} voter(s) over the {from_atomic_formatted(VOTE_CAP, 0)} SXP vote cap:"
        )
        for logging_message in logging_messages:
            print(logging_message)
    else:
        send_messages(voters_to_message)
        print(
            f"Sent message to {voters_to_message_count} voter(s) over the {from_atomic_formatted(VOTE_CAP, 0)} SXP vote cap"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as m_e:
        handle_error(m_e, f"Top level failure", False)
        raise m_e
