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

TICKET_QS_SCORE_OUTPUT_SCHEMA = DataFrameSchema({
    'user': Column(str, nullable=False),
    'qs_score': Column(float, nullable=False, checks=Check.in_range(0, 100)),
})


NAMES_DATA_OUTPUT_SCHEMA = DataFrameSchema({
    'id': Column(int, nullable=False),
    'name': Column(str, nullable=False),
    'phone': Column(str, nullable=False),
    'chat': Column(str, nullable=False),
    'email_address': Column(str, nullable=False),
    'todo_file': Column(str, nullable=False),
}, strict=True)


TODO_OUTPUT_SCHEMA = DataFrameSchema({
    'emails': Column(str, nullable=True),
    'to_do': Column(str, nullable=True),
}, strict=True)


TODO_SUMMARY_OUTPUT_SCHEMA = DataFrameSchema({
    'user': Column(str, nullable=False),
    'emails_count': Column(int, checks=GTE_ZERO, nullable=False),
    'todos_count': Column(int, checks=GTE_ZERO, nullable=False),
}, strict=True)


PROD_TABLE_OUTPUT_SCHEMA = DataFrameSchema({
    'user': Column(str, nullable=False),
    'emails_count': Column(int, checks=GTE_ZERO, nullable=False),
    'todos_count': Column(int, checks=GTE_ZERO, nullable=False),
    'total_chats': Column(int, checks=GTE_ZERO, nullable=False),
    'total_calls': Column(int, checks=GTE_ZERO, nullable=False),
    'total': Column(int, checks=GTE_ZERO, nullable=False),
    'qs_score': Column(float, nullable=True, checks=Check.in_range(0, 100)),
}, strict=True)
