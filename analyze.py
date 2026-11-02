"""Use SQL + Python to evaluate a synthetic training-app funnel and illustrative A/B split."""
import csv
import math
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
FIG = ROOT / 'figures'
FIG.mkdir(exist_ok=True)

def load_table(conn, table, file_name, columns):
    with (DATA / file_name).open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    placeholders = ', '.join('?' for _ in columns)
    conn.executemany(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        [tuple(r[c] for c in columns) for r in rows],
    )

def main():
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE users (user_id TEXT PRIMARY KEY, variant TEXT, channel TEXT, device TEXT, signup_at TEXT)')
    conn.execute('CREATE TABLE events (user_id TEXT, event_name TEXT, event_at TEXT)')
    load_table(conn, 'users', 'users.csv', ['user_id','variant','channel','device','signup_at'])
    load_table(conn, 'events', 'events.csv', ['user_id','event_name','event_at'])
    sql = (ROOT / 'sql' / 'metrics.sql').read_text(encoding='utf-8')
    statements = [q.strip() for q in sql.split(';') if q.strip()]
    print('FUNNEL BY VARIANT')
    funnel = conn.execute(statements[0]).fetchall()
    for variant, n, v, s, k, cr in funnel:
        print(f'variant={variant} signups={n}, plan={v}, start={s}, finish={k}, finish_rate={cr:.2f}%')
    print('\nCHANNELS')
    channel_rows = conn.execute(statements[1]).fetchall()
    assert sum(row[1] for row in channel_rows) == 4000, 'Channel user count should equal total users'
    for row in channel_rows:
        print(row)

    import pandas as pd
    user_frame = pd.read_csv(DATA / 'users.csv')
    event_frame = pd.read_csv(DATA / 'events.csv')
    finish_ids = set(event_frame.loc[event_frame['event_name'] == 'workout_finish', 'user_id'])
    user_frame['finished'] = user_frame['user_id'].isin(finish_ids)
    pandas_rates = user_frame.groupby('variant').agg(n=('user_id','count'), finishes=('finished','sum'))
    for variant, n, viewed, started, finished, rate in funnel:
        assert int(pandas_rates.loc[variant, 'n']) == n
        assert int(pandas_rates.loc[variant, 'finishes']) == finished
    print('Pandas cross-check of SQL conversion: passed')

    counts = {row[0]: (row[4], row[1]) for row in funnel}
    k_a, n_a = counts['A']
    k_b, n_b = counts['B']
    p_a, p_b = k_a/n_a, k_b/n_b
    lift = p_b - p_a
    pooled = (k_a+k_b)/(n_a+n_b)
    se_null = math.sqrt(pooled*(1-pooled)*(1/n_a+1/n_b))
    z = lift/se_null
    p_value = math.erfc(abs(z)/math.sqrt(2))
    se_ci = math.sqrt(p_a*(1-p_a)/n_a + p_b*(1-p_b)/n_b)
    ci_lo, ci_hi = lift-1.96*se_ci, lift+1.96*se_ci
    summary = f'''SYNTHETIC TRAINING APP A/B ANALYSIS\n\nVariant A: {k_a}/{n_a} = {p_a:.4%}\nVariant B: {k_b}/{n_b} = {p_b:.4%}\nAbsolute difference B-A: {lift*100:.2f} percentage points\nTwo-sided z-test p-value: {p_value:.3g}\n95% confidence interval (B-A): [{ci_lo*100:.2f}, {ci_hi*100:.2f}] percentage points\n\nIMPORTANT: data are artificially simulated. This does not show a real product improvement.\n'''
    (ROOT / 'RESULTS.txt').write_text(summary, encoding='utf-8')
    print('\n'+summary)

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        labels = ['Signup','View plan','Start workout','Finish workout']
        fig, ax = plt.subplots(figsize=(7,4))
        for variant,n,v,s,k,cr in funnel:
            values = [100, 100*v/n, 100*s/n, 100*k/n]
            ax.plot(labels, values, marker='o', linewidth=2, label=f'Variant {variant}')
        ax.set_ylabel('Share of signed-up users, %')
        ax.set_title('Synthetic training-app funnel')
        ax.set_ylim(0, 105)
        ax.grid(alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(FIG/'funnel.png', dpi=180)
        plt.close(fig)
    except ImportError:
        print('matplotlib not installed; chart skipped')
    conn.close()

if __name__ == '__main__':
    main()
