import logging

import pandas as pd


def get_total_row(df) -> dict:
    """Getting the final total row"""
    total_row = {
        'user': 'Total',
        'chats_count': df['chats_count'].sum(),
        'calls_count': df['calls_count'].sum(),
        'emails_count': df['emails_count'].sum(),
        'todo_counts': df['todo_counts'].sum(),
        'total': df['total'].sum(),
        'qs': round(df['qs'].mean(), 2),
    }

    logging.info('Received total row for the final table.')

    return total_row


def get_final_prod_df(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame | None:
    """Generating the final productivity table"""
    logging.info('Creating the final productivity table.....')
    merged_df = next(iter(dfs.values()), None)

    if merged_df is None:
        logging.info("No Data in merged_df found!")
        return None

    for df in list(dfs.values())[1:]:
        merged_df = merged_df.merge(
            df,
            how='left',
            on='user',
            validate='one_to_one'
        )

    merged_df = merged_df.fillna(value=0)
    total_counts = ['chats_count', 'calls_count', 'emails_count', 'todo_counts']
    merged_df['total'] = merged_df[total_counts].sum(axis=1)
    merged_df = merged_df[['user', 'chats_count', 'calls_count', 'emails_count', 'todo_counts', 'total','qs']]
    total_row = get_total_row(merged_df)
    merged_df.loc[len(merged_df)] = total_row

    logging.info('Final productivity table created.')

    return merged_df


