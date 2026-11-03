import sqlite3
import pandas as pd

def execute_sql_checks():
    conn = sqlite3.connect("data/placements.db")
    with open("sql/analysis_queries.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()

    queries = [q.strip() for q in sql_script.split(";") if q.strip()]
    for idx, query in enumerate(queries, 1):
        print(f"\n{'='*80}\nEXECUTING ANALYTICAL SQL QUERY #{idx}\n{'='*80}")
        df_res = pd.read_sql_query(query, conn)
        print(df_res.head(15).to_string(index=False))
        print(f"\n[Total Rows Returned: {len(df_res)}]")

    conn.close()

if __name__ == "__main__":
    execute_sql_checks()
