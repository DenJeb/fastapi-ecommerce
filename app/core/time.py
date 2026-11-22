import datetime


def utc_now() -> datetime.datetime:
    """MySQL DATETIME 不保存时区，统一存 UTC 的 naive 时间"""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)