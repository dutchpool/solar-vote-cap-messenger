from typing import Optional

import requests

from api import Pagination
from config import API_BASE_URL


class NodeStatus(object):
    def __init__(self, synced: bool, now: int, blocks_count: int, timestamp: int):
        self.synced: bool = synced
        self.now: int = now
        self.blocks_count: int = blocks_count
        self.timestamp: int = timestamp


class Peer(object):
    def __init__(self, ip: str, port: int, version: str, height: int, latency: int):
        self.ip: str = ip
        self.port: int = port
        self.version: str = version
        self.height: int = height
        self.latency: int = latency


class VotingFor(object):
    def __init__(self, username: str, percent: float, votes: int):
        self.username: str = username
        self.percent: float = percent
        self.votes: int = votes


class Wallet(object):
    def __init__(self, address: str, public_key: str, username: Optional[str], balance: int, nonce: int,
                 voting_for: [VotingFor]):
        self.address: str = address
        self.public_key: str = public_key
        self.username: Optional[str] = username
        self.balance: int = balance
        self.nonce: int = nonce
        self.voting_for: [VotingFor] = voting_for


def parse_node_status(data) -> NodeStatus:
    return NodeStatus(
        synced=data["synced"],
        now=data["now"],
        blocks_count=data["blocksCount"],
        timestamp=data["timestamp"]
    )


def parse_peer(data) -> Peer:
    return Peer(
        ip=data["ip"],
        port=data["port"],
        version=data["version"],
        height=data["height"],
        latency=data["latency"]
    )


def parse_peers(data) -> [Peer]:
    return list(map(lambda entry: parse_peer(entry), data))


def parse_voting_for(data) -> [VotingFor]:
    voting_for: [VotingFor] = []
    for username, voting_for_data in data.items():
        voting_for.append(VotingFor(
            username=username,
            percent=voting_for_data["percent"],
            votes=int(voting_for_data["votes"])
        ))
    return voting_for


def parse_wallet(data_entry) -> Wallet:
    username = None
    if "attributes" in data_entry:
        attributes = data_entry["attributes"]
        if "delegate" in attributes:
            username = attributes["delegate"]["username"]
    return Wallet(
        address=data_entry["address"],
        public_key=data_entry["publicKey"] if "publicKey" in data_entry else None,
        username=username,
        balance=int(data_entry["balance"]),
        nonce=int(data_entry["nonce"]),
        voting_for=parse_voting_for(data_entry["votingFor"])
    )


def parse_wallets(data) -> [Wallet]:
    return list(map(lambda entry: parse_wallet(entry), data))


def get_node_status() -> NodeStatus:
    uri = API_BASE_URL + "/node/status"
    response = requests.get(uri, timeout=10)
    response.raise_for_status()

    json_response = response.json()
    return parse_node_status(json_response["data"])


def get_peers(pagination: Pagination = None) -> [Peer]:
    if pagination is None:
        pagination = Pagination(
            API_BASE_URL + "/peers"
        )
    uri = pagination.get_uri()
    response = requests.get(uri, timeout=10)
    if response.status_code != 200:
        return pagination.result

    json_response = response.json()
    next = json_response["meta"]["next"]
    result = parse_peers(json_response["data"])
    if next is None:
        return pagination.to_result(result)
    else:
        return get_peers(pagination.to_next(API_BASE_URL + next, result))


def get_voters(username: str, pagination: Pagination = None) -> [Wallet]:
    if pagination is None:
        pagination = Pagination(
            f"{API_BASE_URL}/delegates/{username}/voters"
        )
    uri = pagination.get_uri()
    response = requests.get(uri)
    if response.status_code != 200:
        return pagination.result

    json_response = response.json()
    next = json_response["meta"]["next"]
    result = parse_wallets(json_response["data"])
    if next is None:
        return pagination.to_result(result)
    else:
        return get_voters(username, pagination.to_next(API_BASE_URL + next, result))
