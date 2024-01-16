import datetime
from datetime import timezone

def snowflake_to_timestamp(snowflake_id):
    discord_epoch = 1420070400000
    timestamp = ((snowflake_id >> 22) + discord_epoch) / 1000.0
    return datetime.datetime.fromtimestamp(timestamp, tz=timezone.utc)