# Casino

This command lets users play blackjack, roulette, and slots with virtual currency, check their balance and profile, claim a daily reward, and view a leaderboard.

## Overview

Casino currency is virtual only. It has no real-money value, cannot be bought or sold, and exists solely for entertainment on the server. Balances and stats are stored locally and are separate for every user.

## Configuration

The following configuration options are available:

| Option                     | Type        | Description                                                                                       |
| -------------------------- | ----------- | ------------------------------------------------------------------------------------------------- |
| `trigger`\*                | `str`       | The trigger that will be used to invoke the command.                                              |
| `description`              | `str`       | The description that will be displayed in the help command.                                      |
| `data_dir`                 | `str`       | The directory where player data is stored. Defaults to `"casino"`.                                |
| `currency_name`            | `str`       | The name of the currency shown in replies. Defaults to `"chips"`.                                 |
| `currency_symbol`          | `str`       | A symbol prefixed to amounts. Defaults to `""`, which shows the currency name instead.           |
| `starting_balance`         | `int`       | The balance a new player starts with. Defaults to `500`.                                          |
| `daily_reward`             | `int`       | The amount awarded by the daily command. Defaults to `100`.                                       |
| `daily_cooldown`           | `int`       | The time in seconds between daily rewards. Defaults to `86400` (24 hours).                        |
| `min_bet`                  | `int`       | The smallest allowed bet. Defaults to `1`.                                                        |
| `max_bet`                  | `int`       | The largest allowed bet. Defaults to `10000`.                                                     |
| `leaderboard_size`         | `int`       | The maximum number of entries on the leaderboard. Defaults to `10`.                               |
| `blackjack_payout`         | `float`     | The payout multiplier for a natural blackjack. Defaults to `1.5` (3:2).                           |
| `blackjack_decks`          | `int`       | The number of decks in the blackjack shoe. Defaults to `1`.                                      |
| `dealer_hits_soft_17`      | `bool`      | Whether the dealer hits on a soft 17. Defaults to `False`.                                        |
| `slots_symbols`            | `list[str]` | The slot symbols. Defaults to `["cherry", "lemon", "bell", "bar", "seven"]`.                      |
| `slots_weights`            | `list[int]` | The relative weight of each slot symbol. Defaults to `[30, 25, 20, 15, 10]`.                       |
| `slots_payouts`            | `dict`      | The multiplier for three matching symbols. Defaults to `{"cherry": 4, "lemon": 5, "bell": 10, "bar": 20, "seven": 50}`. |
| `slots_two_cherry_payout`  | `int`       | The multiplier for exactly two cherries. Defaults to `2`.                                        |

Options marked with an asterisk (`*`) are required.

## Usage

To use this command, enable it by adding it to the `CommandHandler.commands` section in the `config.py` file.

```python
PLUGINS_CONFIG = {
    "CommandHandler": {
        "prefix": "!",
        "check_interval": 1,
        "commands": {
            "Casino": {
                "trigger": "casino",
                "description": "Play casino games with virtual currency.",
                "data_dir": "casino",
                "currency_name": "chips",
                "currency_symbol": "",
                "starting_balance": 500,
                "daily_reward": 100,
                "daily_cooldown": 86400,
                "min_bet": 1,
                "max_bet": 10000,
                "leaderboard_size": 10,
                "blackjack_payout": 1.5,
                "blackjack_decks": 1,
                "dealer_hits_soft_17": False,
                "slots_symbols": ["cherry", "lemon", "bell", "bar", "seven"],
                "slots_weights": [30, 25, 20, 15, 10],
                "slots_payouts": {"cherry": 4, "lemon": 5, "bell": 10, "bar": 20, "seven": 50},
                "slots_two_cherry_payout": 2,
            },
        },
    },
}
```

## Syntax

Every subcommand can be written in full or as a shortcut.

```text
help
?
balance
bal
daily
profile
leaderboard [count]
lb [count]
top [count]
roulette <bet> <selection>
rl <bet> <selection>
slots <bet>
slot <bet>
blackjack [bet]
bj [bet]
hit
h
stand
s
double
d
```

- `help` shows the command usage.
- `balance` shows your current balance.
- `daily` claims your daily reward.
- `profile` shows your balance, rank, and statistics.
- `leaderboard` shows the top players. An optional count is capped at `leaderboard_size`.
- `roulette` spins the roulette wheel with a bet and a selection.
- `slots` spins the slot reels with a bet.
- `blackjack` starts a hand with a bet, or shows your active hand when no bet is given.
- `hit`, `stand`, and `double` play your active blackjack hand.

## Currency

New players start with `starting_balance`. The `daily` command grants `daily_reward` once per `daily_cooldown` seconds. Bets must be at least `min_bet`, at most `max_bet`, and no greater than your current balance, so balances never go negative.

```text
!casino balance
!casino daily
```

## Roulette

Roulette uses a European single-zero wheel with numbers `0` through `36`. `0` is green, and the other numbers are red or black.

Selections:

- A number from `0` to `36` pays `35:1`.
- `red`, `black`, `odd`, `even`, `low` (`1`–`18`), and `high` (`19`–`36`) pay `1:1`.
- `dozen1`, `dozen2`, and `dozen3` cover `1`–`12`, `13`–`24`, and `25`–`36` and pay `2:1`.
- `column1`, `column2`, and `column3` pay `2:1`.

Zero loses every even-money, dozen, and column bet.

```text
!casino roulette 100 red
!casino roulette 50 dozen2
!casino roulette 25 17
```

## Slots

Slots spin three weighted reels. The default symbols and weights are `cherry` 30, `lemon` 25, `bell` 20, `bar` 15, and `seven` 10.

Payouts are total return multipliers on the stake:

- Three `cherry` pays `4x`.
- Three `lemon` pays `5x`.
- Three `bell` pays `10x`.
- Three `bar` pays `20x`.
- Three `seven` pays `50x`.
- Exactly two `cherry` pays `2x`.

```text
!casino slots 100
```

## Blackjack

Blackjack hands persist until they are finished. Use `hit` to draw, `stand` to end your turn, or `double` to double the bet and draw one card. Double is only allowed on the first two cards of a hand. A natural blackjack pays `blackjack_payout` (default `1.5`, or 3:2) rounded down. The dealer stands on soft 17 by default. There is no split and no insurance. A push returns the stake. An active hand survives a restart of the bot. Running `!casino blackjack` with no bet shows your current hand.

```text
!casino blackjack 100
!casino hit
!casino stand
!casino double
```

## Leaderboard

The leaderboard lists the players with the highest balances, up to `leaderboard_size`. Players with equal balances are ordered by wins and then by name.

## Persistence

Player data is stored as one JSON file per user at `<data_dir>/players/<sha256(uid)>.json`. Each file includes a schema version, the real UID, the balance, the ledger total, statistics, the transaction history, and any active blackjack hand. Writes are atomic. Corrupt player files are quarantined, and a corrupt file does not affect other players.

## Limitations

- Currency is virtual only and has no real-world value.
- Game outcomes are random.
- There is no poker, no achievements, and no badges.
- There is no session timeout.
- An active blackjack hand only blocks another blackjack hand; it does not block roulette or slots.
- Only one bot process should use a given data directory at a time.
- Storage write failures are logged but may not reach the player.
