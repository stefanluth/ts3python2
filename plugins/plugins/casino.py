import functools
import threading

from nanoSQLite import NanoSQLite

from ts3client.user.user import User

from ..plugin import Plugin


class Casino(Plugin):
    db = NanoSQLite("casino")
    wage: int = 10
    starting_balance: int = 500
    apply_wages_thread: threading.Thread | None
    add_players_thread: threading.Thread | None

    def run(self, wage: int, starting_balance: int):
        """Run the casino.

        :param wage: The amount of money to wage.
        :type wage: int
        :param starting_balance: The starting balance for each client.
        :type starting_balance: int
        """
        self.client.enable_events_and_messages()
        self.db.create_table(
            "players",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "uid": "TEXT",
                "name": "TEXT",
                "balance": "INTEGER",
                "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            },
        )
        self.db.create_table(
            "transactions",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "uid": "TEXT",
                "amount": "INTEGER",
                "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            },
        )

        self.wage = wage
        self.starting_balance = starting_balance

        self.apply_wages_thread = threading.Thread(target=self.apply_wages_loop)
        self.add_players_thread = threading.Thread(target=self.add_players_loop)

    def event_loop(interval: int):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self: "Casino", *args, **kwargs):
                while not self.event.is_set():
                    func(self, *args, **kwargs)
                    self.event.wait(interval)

            return wrapper

        return decorator

    def user_loop(func):
        @functools.wraps(func)
        def wrapper(self: "Casino", *args, **kwargs):
            for user in self.client.get_users():
                func(self, user, *args, **kwargs)

        return wrapper

    @event_loop(interval=1)
    @user_loop
    def apply_wages_loop(self, user):
        player = self.db.select_first("players", ["uid"], {"uid": user.client_unique_identifier})
        if not player:
            return

        self.logger.debug(f"Applying wage to {user.client_nickname} ({user.client_unique_identifier})")
        self.add_balance(user, self.wage, True)

    @event_loop(interval=10)
    @user_loop
    def add_players_loop(self, user):
        player = self.db.select_first("players", ["uid"], {"uid": user.client_unique_identifier})
        if player:
            return

        self.logger.debug(f"Adding player {user.client_nickname} ({user.client_unique_identifier})")
        self.add_player(user)

    def add_player(self, user: User):
        self.db.insert(
            "players",
            {
                "uid": user.client_unique_identifier,
                "name": user.client_nickname,
                "balance": self.starting_balance,
            },
        )

        self.db.insert(
            "transactions",
            {
                "uid": user.client_unique_identifier,
                "amount": self.starting_balance,
            },
        )

    def get_balance(self, user: User) -> int:
        return self.db.select_first("players", ["balance"], {"uid": user.client_unique_identifier}).get("balance")

    def add_balance(self, user: User, amount: int, sanity_check: bool = False):
        self.db.update(
            "players",
            {"balance": self.get_balance(user) + amount},
            {"uid": user.client_unique_identifier},
        )

        self.db.insert(
            "transactions",
            {
                "uid": user.client_unique_identifier,
                "amount": amount,
            },
        )

        if sanity_check:
            self.sanity_check(user)

    def sanity_check(self, user: User):
        """Check the balance of a player against their transactions.

        :param user: The user to check.
        :type user: User
        """

        balance = self.db.select_first("players", ["balance"], {"uid": user.client_unique_identifier}).get("balance")
        transactions: list[dict] = self.db.select("transactions", ["amount"], {"uid": user.client_unique_identifier})
        transactions_sum = sum([transaction["amount"] for transaction in transactions])

        if balance != transactions_sum:
            raise ValueError(
                f"Balance {balance} does not match transactions sum {transactions_sum} for user {user.client_unique_identifier} ({user.client_nickname})"
            )
