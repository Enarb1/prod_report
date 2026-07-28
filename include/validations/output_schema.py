from pandera.pandas import Column, DataFrameSchema, Check

from include.validations.validations_checks import GTE_ZERO



CHAT_DATA_OUTPUT_SCHEMA = DataFrameSchema({
    'record_id': Column(int, nullable=False),
    'user': Column(str, nullable=False),
}, strict=True)


CHAT_TRANSFORMED_OUTPUT_SCHEMA = DataFrameSchema({
    'user': Column(str, nullable=False),
    'total_chats': Column(int, nullable=False, checks=GTE_ZERO),
}, strict=True)


PHONE_DATA_OUTPUT_SCHEMA = DataFrameSchema({
    'user': Column(str, nullable=False),
    'total_calls': Column(int, nullable=False, checks=GTE_ZERO),
}, strict=True)


TICKET_QS_OUTPUT_SCHEMA = DataFrameSchema({
    'ticket_id': Column(str, nullable=False),
    'quality_pass': Column(str, nullable=False, checks=Check.isin(["in ordnung", "durchgefallen"] )),
    'user': Column(str, nullable=False),
}, strict=True)


NAMES_DATA_OUTPUT_SCHEMA = DataFrameSchema({
    'id': Column(int, nullable=False),
    'name': Column(str, nullable=False),
    'phone': Column(str, nullable=False),
    'chat': Column(str, nullable=False),
    'email_address': Column(str, nullable=False),
    'todo_file': Column(str, nullable=False),
}, strict=True)


TODO_OUTPUT_SCHEMA = DataFrameSchema({
    'emails': Column(str),
    'to_do': Column(str),
}, strict=True)
