from pandera.pandas import  Column, DataFrameSchema

CHAT_DATA_INPUT_SCHEMA = DataFrameSchema({
    'RecordId': Column(str, nullable=False),
    'ParentRecordId': Column(float),
    'ChildRecordId': Column(float, nullable=True),
    'CustomerId': Column(str),
    'RequestStatus': Column(str),
    'ExitCode': Column(str),
    'EmployeeName': Column(str, nullable=False),
    'UserId': Column(str),
    'GroupName': Column(str),
    'PrimaryGroupName': Column(str),
    'RequestTime': Column(str),
    'WaitTime': Column(float),
    'ServeTime': Column(str),
    'EndTime': Column(str),
    'ServiceSeconds': Column(float),
    'Endby': Column(str),
    'ITSM Incident No': Column(float),
    'IsOutboundCall': Column(float),
    'useragent': Column(str),
    'virtualagent': Column(float),
    'purgeddate': Column(float),
    'PreChatPurgedDate': Column(float),
    'AttemptCount': Column(float),
    'ContactTaskType': Column(float),
    'actualuseragent': Column(str),
    'Transport': Column(str),
    'WaitCount': Column(float),
    'ServiceCount': Column(float),
    'AgentLoadCount': Column(float),
    'ActiveAgentCount': Column(float),
    'ActiveAgentCountInGroup': Column(float),
    'calltype': Column(str),
    'teams.country': Column(str),
    'teams.locale': Column(str),
})



PHONE_DATA_INPUT_SCHEMA = DataFrameSchema({
        "User": Column(str, nullable=False),
        "Dialing attempts[Number]": Column(int),
        "Accepted calls[Number]": Column(int, nullable=False),
        "Connected  to the caller[Number]": Column(int),
        "Availability[%]": Column(int),
        "Not answered total[Number]": Column(int),
        "Busy[Number]": Column(int),
        "Hang ups customer[Number]": Column(int),
        "max. Ring Time reached[Number]": Column(int),
        "other reasons[Number]": Column(int),
        "... which were forwarded before connect[Number]": Column(int),
        "Connection time user[Min]": Column(str),
        "Ø-Connection time user[s]": Column(float),
        "Call Duration User[Min]": Column(str),
        "Average call duration user[s]": Column(float),
        "Ø-Connection setup user[s]": Column(float),
        "Reaction time user total[s]": Column(int),
        "Ø-Reaction time user[s]": Column(str),
        "Ø-Sum Connection establishment + reaction time user[s]": Column(str,),
        "Wrap-up time[Min]": Column(str),
        "Ø-Wrap-up time[s]": Column(float),
        "Calls <=10s[Number]": Column(int),
        "Forwarding[Number]": Column(int),
        ",,,,,,": Column(str),
})


TICKET_QS_INPUT_SCHEMA = DataFrameSchema(
    {
        "Name ": Column(str),
        "KW": Column(str),
        "Datum": Column('datetime64[ns]'),
        "Ticketnummer": Column(str, nullable=False),
        "Tickettype": Column(str),
        "Richtiger KB": Column(str),
        "Richtige und Vollständige Abarbeitung KB": Column(str),
        "Datenaufnahme (Description)": Column(str),
        "Troubleshooting Performed & Documented": Column(str),
        "Solution nachvollziehbar": Column(str),
        "Priorisierung korrekt": Column(str),
        "Individuelle Betrachtung / Anpassbares Kriterium": Column(str),
        "Ampelstatus Ticket QS": Column(str, nullable=True),
        "Focus - Thema": Column(str),
        "Maßnahme": Column(str),
        "Kommentar": Column(str),
        "Betroffene FG": Column(str),
        "CI": Column(str),
        "Ersteller": Column(str, nullable=True),
        "Verursacher 1": Column(str),
        "Verursacher 2": Column(str),
        "Verursacher 3": Column(str),
        "Umgesetzte Maßnahme": Column(str),
    },)


NAMES_DATA_INPUT_SCHEMA = DataFrameSchema({
    'ID': Column(int, nullable=False),
    'Name': Column(str, nullable=False),
    'Phone': Column(str, nullable=False),
    'Chat': Column(str, nullable=False),
    'Email Address': Column(str, nullable=False),
    'todo_file': Column(str, nullable=False),
})

TODO_INPUT_SCHEMA = DataFrameSchema({
    'Emails': Column(str),
    'ToDo': Column(str),
})










