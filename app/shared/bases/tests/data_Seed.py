import sys

from app.shared.bases.base_model import DataSeeder

args = sys.argv or 1000
DataSeeder(
    number_of_records=int(args[1]),
    exclude_list=[
        # "bet_detail_history",
        # "payment_history",
        # "action_history",
        # "game_list",
        # "balance",
        # "admin",
    ],
).generate()
