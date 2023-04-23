# solar-vote-cap-messenger

Send a message to voters over your vote cap.

## Installation

```
cd ~ && git clone https://github.com/dutchpool/solar-vote-cap-messenger.git
sudo apt install python3-pip
cd ~/solar-vote-cap-messenger && pip3 install -r requirements.txt
```

## Configuration

Configure the values in `config.py`.

- `API_BASE_URL` - The url to an api. Must not be empty and end with `/api`.
- `SYNC_CHECK_ENABLED` - Perform a check if the node is in sync with the network. Failing this check cancels script execution.
- `SYNC_CHECK_BLOCK_THRESHOLD` - The amount of blocks the node may differ from the network before considering it out of sync.
- `BLOCK_PRODUCER_USERNAME` - The block producer username.
- `WALLET_MNEMONIC` - Mnemonic of the wallet to send the message from.
- `WALLET_SECOND_MNEMONIC` - Second mnemonic of the wallet to send the message from, or `None`.
- `VOTE_CAP` - The vote weight threshold used for selecting voters to receive the message.
- `MESSAGE` - The message to send to voters over the vote cap.
- `MESSAGE_INTERVAL_SECONDS` - The interval in seconds to repeat sending the message. Set `MESSAGE_LIMIT_PER_VOTER` to `1` to send the message only once.
- `MESSAGE_LIMIT_PER_VOTER` - The maximum amount of messages to send to one voter. Set to `-1` to set no maximum.

## Crontab

Create a `crontab -e` entry at the desired time and interval, e.g. every 15 minutes. This chosen interval determines how fast the script responds to new voters. The interval of repeated messages is dictated by `config.py`'s `MESSAGE_INTERVAL_SECONDS`.

```
*/15 * * * * cd ~/solar-vote-cap-messenger && python3 ~/solar-vote-cap-messenger/messenger.py > /dev/null 2>&1
```

## Usage

### Steps taken by the script

- Get the voters from the api and check if there are new voters over the vote cap.

- If a new voter is over the vote cap, send a message right away, unless the repeating message interval is coming up soon.

- If an already known voter is over the cap, send a message if `MESSAGE_INTERVAL_SECONDS` has passed and `MESSAGE_LIMIT_PER_VOTER` has not yet been reached.

### Run the script once

```
messenger.py

Arguments:
- test, optional: -t | --test  # Run the script in test mode, no messages will be sent.
- set time, optional: -st <HH:MM> | --settime <HH:MM>  # Change the time of day when the repeated message is sent.

Examples:
python3 messenger -t
python3 messenger -st 13:00
```
