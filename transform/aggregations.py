import logging

import pandas as pd


def get_quality_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Getting quality scores for each agent"""

    qs_score  = df.assign(
        is_passing=lambda x:
        x['ampelstatus_ticket_qs'].eq('in Ordnung')
    ).groupby('user').agg(
        total_tickets=('ticketnummer', 'count'),
        passing_tickets=('is_passing', 'sum'),
    ).assign(
        qs=lambda x:
        (x['passing_tickets'] / x['total_tickets'] * 100).round(2)
    ).reset_index().sort_values(by='user')

    logging.info('Aggregated Quality scores!')

    return qs_score


def get_chat_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Getting chat counts for each agent"""

    chats_count = (df
                   .groupby('user')
                   .agg(
        chats_count=('record_id', 'count'))
                   .reset_index()
                   .sort_values(by='user'))

    logging.info('Aggregated Chat counts!')

    return chats_count


def get_aggregations(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Getting the chat counts, phone counts and the quality scores for the agents"""
    agg_mapper = {
        'chat': get_chat_counts,
        'quality': get_quality_scores,
    }

    agg_dfs = {}

    for df_type, df in dfs.items():
        if df_type == 'phone':
            agg_dfs[df_type] = df
            logging.info("Phone counts added!")
            continue
        agg_df = agg_mapper[df_type](df)
        agg_dfs[df_type] = agg_df


    return agg_dfs


def get_todo_aggregations(todo_dfs: dict[str, pd.DataFrame], names_df: pd.DataFrame) -> pd.DataFrame:
    """Getting the email and todo counts for the agents"""
    names_mapper = names_df.set_index('todo_file')["Name"]
    rows = []

    for file_name, df in todo_dfs.items():
        name = names_mapper.get(file_name)
        if name is None:
            logging.error(f'No name for {file_name} found!')
            continue

        counts = df[['emails', 'to_do']].count()
        rows.append({
            'user': names_mapper.get(file_name, ''),
            'emails_count': counts['emails'],
            'todo_counts': counts['to_do']
        })

    todo_summary = pd.DataFrame(rows)

    return todo_summary
