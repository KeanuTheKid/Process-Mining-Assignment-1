import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Assignment 1 – Road Traffic Fine Management

    **Part 1** (Sessions 1–3) · Process Mining HS26 · Keanu Belo da Silva

    Quick note on how I worked: before running a cell I wrote down what I expected (*Hypothesis*), then compared it with the result.
    Things that came up along the way are collected as **Finding** (something that could be improved in the process or the data) or **Open question**.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import pm4py
    import plotly.express as px  

    pd.set_option('display.max_columns', 30)
    return mo, pd, pm4py, px


@app.cell
def _(pm4py):
    event_log_from_disk = pm4py.read_xes('Road_Traffic_Fine_Management_Process.xes', variant="rustxes")

    print(len(event_log_from_disk), 'events read.')
    return (event_log_from_disk,)


@app.cell
def _(event_log_from_disk):
    # some short names, and sort events per case by time (stable, so same-day events keep their file order)
    C = 'case:concept:name'
    A = 'concept:name'
    T = 'time:timestamp'

    log = event_log_from_disk.sort_values([C, T], kind='stable').reset_index(drop=True)
    log[T + ':local'] = log[T].dt.tz_convert('Europe/Rome')
    log.head()
    return A, C, T, log


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 1

    ## Task 1.1
    """)
    return


@app.cell
def _(T, log):
    print('first event (UTC):  ', log[T].min())
    print('last event (UTC):   ', log[T].max())
    print('first event (Italy):', log[T + ':local'].min())
    print('last event (Italy): ', log[T + ':local'].max())
    print()
    print(log[T + ':local'].dt.year.value_counts().sort_index())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **a) Time interval.** The log goes from **1 Jan 2000 to 18 Jun 2013**, so roughly 13 and a half years.
    log gave back UTC but Italy is in another time zone.

    The number of events per year is quite stable until about 2011 and then drops. 2013 is only half a year, but 2012 is also clearly lower → probably many cases from the last years are still running when the log was cut.
    """)
    return


@app.cell
def _(log):
    print(log['vehicleClass'].nunique(), 'distinct values')
    log['vehicleClass'].value_counts(dropna=False)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **b) vehicleClass** has **4 distinct values**: A (146'712), C (2'456), M (1'198) and R (only 4). The rest is NaN because the attribute only exists on *Create Fine*.
    The log doesn't explain the codes. My guess is A = Auto (car), M = Motorbike, C = commercial vehicles / trucks, R = (I am not sure)
    """)
    return


@app.cell
def _(A, C, log):
    create = log[log[A] == 'Create Fine']
    print('min   ', create['amount'].min())
    print('median', create['amount'].median())
    print('max   ', create['amount'].max())
    print()
    print('fines with amount 0:', (create['amount'] == 0).sum())
    print('articles of the 0 fines:', create[create['amount'] == 0]['article'].value_counts().to_dict())
    print()
    print('10 largest:')
    print(create.nlargest(10, 'amount')[[C, 'article', 'amount']].to_string(index=False))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **c) Initial amount:** min **0**, median **35**, max **4'351**.

    *Hypothesis before:* typical parking-ticket amounts, so somewhere between 20 and 100, maybe some higher ones. The median fits that.

    What I'd look at more closely:
    - **36 fines with amount 0.** A fine of 0 € doesn't make much sense. Either data error, or the fine was cancelled/converted right away. They are spread over many different articles, so it's not one specific offence.
    - **The upper tail**: a few fines above 1'000 €, max 4'351. Mostly articles: 23(illegal ads by the road), 213(driving with a confiscated car).
    - The difference between mean (~45) and median (35) already shows the distribution is very skewed -> mean is not a good summary here.
    """)
    return


@app.cell
def _(A, C, log):
    with_points = log[log['points'] > 0]
    print('events with points > 0:', len(with_points))
    print('cases affected:        ', with_points[C].nunique())
    print(with_points[A].value_counts())
    print()
    print(with_points['points'].value_counts().sort_index())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **d) Points.** **3'548 events** have points > 0. All of them are *Create Fine* (the attribute only exists there), so it's also exactly **3'548 cases**.
    That is only about 2.4% of all fines, so most fines in this log don't cost any license points (makes sense for parking).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 2

    ## Task 2.1 – Timestamp granularity
    """)
    return


@app.cell
def _(T, log):
    local = log[T + ':local']
    print('events not at midnight (local):', (local.dt.hour != 0).sum())
    print('events with minutes/seconds:   ', ((local.dt.minute != 0) | (local.dt.second != 0)).sum())
    print()
    print('UTC hours used:')
    print(log[T].dt.hour.value_counts())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Granularity is **days**. Every single timestamp is exactly midnight Italian time (22:00 or 23:00 UTC depending on summer time).

    This has consequences: if two events of a case happen on the same day we don't know their real order. In the sorted log there are around 12k events that share the day with another event of the same case.

    **Finding:** record the real time (or at least a sequence number per case). Otherwise you can't tell e.g. whether a payment came before or after the penalty on the same day.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.2 – Activity schemas

    I counted per activity how many events actually have a value for each attribute.
    (I also parsed the raw XES file once to be sure that pandas didn't hide anything: an attribute that is "missing" in pandas is really absent in the XES too.)
    """)
    return


@app.cell
def _(A, T, log):
    attrs = [c for c in log.columns if c not in [A, T, T + ':local', 'case:concept:name', 'lifecycle:transition']]
    schema = log.groupby(A)[attrs].apply(lambda g: g.notna().sum())
    events_per_activity = log[A].value_counts()
    schema.insert(0, '#events', events_per_activity)
    # only keep attributes that are used by at least one event of that activity
    schema
    return attrs, schema


@app.cell
def _(attrs, schema):
    # attribute is "in the schema" of an activity if at least one event has it
    # missing = in the schema but not on every event
    missing = []
    for act, row in schema.iterrows():
        for att in attrs:
            if 0 < row[att] < row['#events']:
                missing.append((act, att, row['#events'] - row[att]))
    missing
    return


@app.cell
def _(attrs, schema):
    # in how many activity schemas does each attribute appear?
    (schema[attrs] > 0).sum().sort_values(ascending=False)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **a) Missing values.** Only one real case: **`lastSent` on *Insert Fine Notification* is missing for 1'631 events** (78'229 of 79'860 have it).

    Two things that are not technically missing but kind of are:
    - `matricola` on *Appeal to Judge* is always **0** – a column with only one value carries no information (description also says N/A).
    - `dismissal = NIL` means "not dismissed / nothing", so it's a placeholder, not really a value.

    **b) Shared non-global attributes.** Global are only `concept:name`, `time:timestamp`, `lifecycle:transition`. Shared by more than one activity are:

    | attribute | activities | numerical? | type |
    |---|---|---|---|
    | `amount` | Create Fine, Add penalty | yes | **cumulative** |
    | `totalPaymentAmount` | Create Fine, Payment | yes | **cumulative** |
    | `dismissal` | Create Fine, Send Appeal to Prefecture, Appeal to Judge | no | – |
    | `org:resource` | Create Fine, Appeal to Judge | no (it's an ID) | – |

    Why `amount` is cumulative: at *Add penalty* the amount is about **2×** the initial amount (median ratio 2.04), so it's the new total including the penalty and not only the penalty itself. That fits the description ("amount incl. penalty").
    `totalPaymentAmount` is cumulative by name and starts with 0 at Create Fine (checked in 2.4).
    The incremental counterparts would be `paymentAmount` (one payment) and `expense` – but those only appear in one schema each.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.3 – Inspecting one case
    """)
    return


@app.cell
def _(A, C, T, log):
    show_cols = [A, T + ':local', 'amount', 'expense', 'paymentAmount', 'totalPaymentAmount', 'dismissal',
                 'notificationType', 'lastSent', 'article', 'points', 'vehicleClass', 'org:resource']

    def show_case(case_id, cols=show_cols):
        return log[log[C] == case_id][cols]

    show_case('A100')
    return show_case, show_cols


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Case **A100** (5 events, takes almost 3 years):

    - **2.8.2006 – Create Fine:** a car (class A) gets a fine of 35 € for article 157 (parking), 0 points, entered by resource 561. Not dismissed (NIL), nothing paid yet.
    - **12.12.2006 – Send Fine:** fine is sent by post, more than 4 months later. 11 € postal expenses get added.
    - **15.1.2007 – Insert Fine Notification:** about a month later the notification is registered → offender now officially knows. It was delivered to the owner of the car (type P). `lastSent = P` too.
    - **16.3.2007 – Add penalty:** exactly 60 days after the notification, nothing was paid → amount goes up to 71.50 € (roughly doubled).
    - **30.3.2009 – Send for Credit Collection:** two years later still nothing paid, so it is handed over to the credit collection agency. Outstanding at that point: 71.50 + 11 = 82.50 €.

    Interesting: the 60 days between notification and penalty look like a fixed rule. And it takes 4 months just to send the letter.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.4 – Cumulative payments

    *Hypothesis:* should be identical to `totalPaymentAmount` – maybe a few rounding differences.

    I did it vectorized with `groupby().cumsum()` instead of `track_variables` from the course code, because `iterrows` over 560k events is pretty slow. Same idea though.
    """)
    return


@app.cell
def _(C, log):
    log['payment_cum'] = log['paymentAmount'].fillna(0).groupby(log[C]).cumsum().round(2)
    return


@app.cell
def _(show_case, show_cols):
    # a) a case with three payments on different days
    show_case('A12991', show_cols + ['payment_cum'])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    a) A12991 has three payments: 49 → +38 → +38, so payment_cum goes 49 → 87 → 125, and totalPaymentAmount says exactly the same on each event. Events without a payment just keep the previous value (0 before the first payment). Looks right.

    Side note: the person owed 36 + 13 postage, then the penalty brought it to 74 + 13 = 87. So after the second payment everything was paid, and the third payment of 38 is too much. That's one of the negative outstanding_amount cases from 2.5.
    """)
    return


@app.cell
def _(A, C, T, log):
    payments = log[log[A] == 'Payment'].copy()
    payments['deviation'] = (payments['payment_cum'] - payments['totalPaymentAmount']).round(2)
    deviating = payments[payments['deviation'] != 0]

    print('payment events:          ', len(payments))
    print('deviating payment events:', len(deviating))
    print('deviating cases:         ', deviating[C].nunique())
    print('deviation > 0:', (deviating['deviation'] > 0).sum(), '| deviation < 0:', (deviating['deviation'] < 0).sum())
    print('sum of deviations:', deviating['deviation'].sum().round(2))
    print()

    # explanation 1: several payments on the same day
    payments['n_same_day'] = payments.groupby([C, T])[A].transform('size')
    print('deviating events with another payment on the same day:', (deviating.index.isin(payments[payments['n_same_day'] > 1].index)).sum())

    # explanation 2: the difference is exactly one payment amount
    first_dev = deviating.groupby(C).first()
    print('cases where the first deviation equals a payment amount:',
          ((first_dev['deviation'] + first_dev['paymentAmount']).round(2) == 0).sum(), 'of', len(first_dev))
    deviating['deviation'].describe()
    return


@app.cell
def _(show_case, show_cols):
    show_case('A12292', show_cols + ['payment_cum'])
    return


@app.cell
def _(show_case, show_cols):
    show_case('A22233', show_cols + ['payment_cum'])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **b)** Not identical. **95 of 77'601 payment events (77 cases) deviate**. And it's always in the same direction: `totalPaymentAmount` is **higher** than my sum, never lower. In total about 5'300 € more.

    Two things seem to happen:
    1. **Same-day payments** (A12292: 49 € and 87 € on the same day). `totalPaymentAmount` already shows 136 on both events, so it's the end-of-day value. That's just the day granularity again, not really an error. After the day both are equal again.
    2. **Real differences in 50 cases.** E.g. A22233: the person owes 49, pays 49, but `totalPaymentAmount` says **98**. Then the penalty comes, they pay the remaining 38 and `totalPaymentAmount` says 136 although only 87 were owed and paid.
       So who is right? I compared both with what was owed at the end (fine + penalty + expenses):
       - in 18 cases the Payment events add up *exactly* to what was owed → looks like `totalPaymentAmount` counted a payment twice
       - in 7 cases it's the other way round → there a Payment event seems to be missing in the log (maybe removed as a "duplicate" during log preparation, since two equal payments on the same day look identical with day timestamps)
       - the rest fits neither

       Also interesting: in 49 of the 77 cases the deviation is exactly one of the payment amounts of that case. So it's almost always "one payment too many or too few", not random numbers.

    I'd say neither of the two attributes is fully reliable, it's only 50 out of 150k cases though.

    **Finding:** payments should have a unique ID (like a payment reference) so you can't double count them or lose them as duplicates.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.5 – Outstanding amount

    What the offender has to pay = current fine amount (incl. penalty if added) + all expenses – all payments so far. I built it in three steps:
    - `amount_latest`: the latest value of `amount` (works since amount is cumulative, see 2.2b)
    - `expense_cum`: cumulative sum of `expense`
    - `outstanding_amount = amount_latest + expense_cum - payment_cum`
    """)
    return


@app.cell
def _(C, log):
    log['amount_latest'] = log.groupby(C)['amount'].ffill()
    log['expense_cum'] = log['expense'].fillna(0).groupby(log[C]).cumsum().round(2)
    log['outstanding_amount'] = (log['amount_latest'] + log['expense_cum'] - log['payment_cum']).round(2)
    return


@app.cell
def _(show_case, show_cols):
    show_case('A10000', show_cols + ['amount_latest', 'expense_cum', 'payment_cum', 'outstanding_amount'])
    return


@app.cell
def _(log):
    print('events with outstanding_amount > 0:', (log['outstanding_amount'] > 0).sum(), 'of', len(log))
    print('= 0:', (log['outstanding_amount'] == 0).sum())
    print('< 0:', (log['outstanding_amount'] < 0).sum())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **a)** A10000: 36 € fine → +13 € postage = 49 → penalty, amount becomes 74 → outstanding 87 → payment of 87 → **0**. Fits perfectly.

    **b)** **500'406 events** (89%) have `outstanding_amount > 0`. Not surprising, because every case starts with an open fine.

    Side observation: **1'271 events are below 0**, so people paid more than the log says they owe. Mostly small amounts (a few cents to a few euros, maybe rounding or postage they calculated differently), but some are big (down to −3'935).
    are there expenses/penalties that are not in the log, or did people really overpay and get refunds?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.5 (Part 3) – Case log + initial fine amount
    """)
    return


@app.cell
def _(A, C, T, log):
    _cases = log.groupby(C)
    case_log = _cases.agg(
        start_time=(T, 'first'),
        end_time=(T, 'last'),
        no_of_events=(A, 'count'),
        initial_amount=('amount', 'first'),
        final_amount=('amount', 'last'),
        total_paid=('payment_cum', 'last'),
        total_expense=('expense_cum', 'last'),
        outstanding_end=('outstanding_amount', 'last'),
        vehicleClass=('vehicleClass', 'first'),
        article=('article', 'first'),
        points=('points', 'first'),
        resource=('org:resource', 'first'),
        dismissal_create=('dismissal', 'first'),
    )
    case_log['duration'] = case_log['end_time'] - case_log['start_time']
    case_log['year'] = case_log['start_time'].dt.tz_convert('Europe/Rome').dt.year
    # how often each activity happens per case
    case_log = case_log.join(log.groupby([C, A]).size().unstack(fill_value=0))
    case_log
    return (case_log,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **a) Hypothesis:** most fines are small parking fines, so I expect a big peak somewhere around 30–40 € and a long tail to the right (few expensive ones). Probably not a smooth curve, since fines come from a fixed catalogue.
    """)
    return


@app.cell
def _(case_log, px):
    px.histogram(case_log[case_log['initial_amount'] <= 200], x='initial_amount', nbins=200,
                 title='Initial fine amount (cases up to 200 € (>99% of all cases))')
    return


@app.cell
def _(case_log, px):
    px.histogram(case_log[case_log['initial_amount'] > 0], x='initial_amount', log_x=True, log_y=True,
                 title='Initial fine amount, log scale (whole range)')
    return


@app.cell
def _(case_log):
    print(case_log['initial_amount'].value_counts().head(10))
    case_log[case_log['article'] == 157].groupby('year')['initial_amount'].median()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **b) Observations:**
    1. It's **not a smooth distribution but a few spikes**. 35, 36, 33.6, 38, 31.3 € alone cover more than half of all cases. That's the parking fine (article 157) in different years.
    2. These spikes move up **over time**: the parking fine was 31.30 in 2000, 35 in 2005, 38 in 2009 and 41 in 2013. So the same offence gets more expensive every ~2 years (Maybe inflation or being stricter with people parking in wrong places). The amount alone tells you a lot about the year.

    Plus, as expected, there's a long tail: a second smaller group around 70–80 € and very few above 1'000 €.
    Hypothesis confirmed regarding the peak + tail. I didn't expect the year effect though.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.6 – Initial vs. final amount
    """)
    return


@app.cell
def _(case_log, px):
    _sample = case_log[(case_log['initial_amount'] > 0)].sample(20000, random_state=1)
    px.scatter(_sample, x='initial_amount', y='final_amount', log_x=True, log_y=True, opacity=0.3,
               title='Initial vs final amount (sample of 20k cases, log-log)')
    return


@app.cell
def _(case_log):
    (case_log['final_amount'] / case_log['initial_amount']).round(1).value_counts().head(6)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    There are basically **two straight lines**:
    - **final = initial** (~70k cases): no penalty. Either paid in time, dismissed, or the case just stopped (e.g. after Send Fine).
    - **final ≈ 2 × initial** (~80k cases incl. the 2.1 ones): penalty added, which roughly doubles the fine.

    Almost nothing in between, so the penalty is not individual but a fixed rule (double the fine, slightly rounded). A handful of cases have 2.5× or 4× (two penalties?)

    The fact that around half of all fines get doubled is quite a lot. People either don't pay in time or don't know they have to.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.7 – Something noteworthy: points over time
    """)
    return


@app.cell
def _(case_log, pd):
    pd.crosstab(case_log['year'], case_log['points'] > 0).rename(columns={False: 'no points', True: 'with points'})
    return


@app.cell
def _(case_log, pd):
    _a158 = case_log[case_log['article'] == 158]
    pd.crosstab(_a158['year'], _a158['points'])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Points only exist from 2003 on.** Between 2000 and 2002 there's not one single fine with points, after that it slowly goes up.
    This fits the introduction of the Italian points license (*patente a punti*) in mid-2003.

    But even after 2003 it's inconsistent: for **article 158** (the same offence) only some fines have 2 points and the majority has 0. Maybe the points depend on something we don't see (e.g. whether the driver was identified, only then you can take points from a person – fits `notificationType` P vs C?).


    Another small one: `org:resource` – 147 different resources, but the top 5 (538, 550, 541, 537, 559) create almost 25% of all fines.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 3 – Outcomes

    ## Task 3.1 – Three business level outcomes

    From the point of view of the police / municipality I'd say these are the three outcomes that matter:

    1. **Paid** – the offender paid everything that was owed (something was paid and outstanding at the end ≤ 0). That's the "good" ending.
    2. **Credit collection** – the fine was handed over to the collection agency. Basically the police gave up collecting themselves.
    3. **Dismissed** – the fine got cancelled, i.e. `dismissal` has a value other than `NIL` in any event of the case (at creation or as result of an appeal, e.g. `#` prefecture, `G` judge).

    *Hypothesis:* roughly half paid, a third credit collection, dismissed small (few %). Overlaps should be rare because these are kind of exclusive endings. But I'd expect a decent amount of cases without outcome, since the last years in the log are probably not finished yet.
    """)
    return


@app.cell
def _(C, case_log, log):
    _dismissed = log.groupby(C)['dismissal'].agg(lambda s: (s.dropna() != 'NIL').any())

    case_log['is_paid'] = (case_log['total_paid'] > 0) & (case_log['outstanding_end'] <= 0)
    case_log['is_credit_collection'] = case_log['Send for Credit Collection'] > 0
    case_log['is_dismissed'] = _dismissed

    outcomes = ['is_paid', 'is_credit_collection', 'is_dismissed']
    return (outcomes,)


@app.cell
def _(case_log, outcomes, pd):
    import itertools

    _rows = {o: case_log[o].sum() for o in outcomes}
    for _a, _b in itertools.combinations(outcomes, 2):
        _rows[_a + ' & ' + _b] = (case_log[_a] & case_log[_b]).sum()
    _rows['all three'] = case_log[outcomes].all(axis=1).sum()
    _rows['no outcome'] = (~case_log[outcomes].any(axis=1)).sum()
    outcome_counts = pd.Series(_rows, name='cases').to_frame()
    outcome_counts['share %'] = (outcome_counts['cases'] / len(case_log) * 100).round(1)
    outcome_counts
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **a)** Out of 150'370 cases:

    - paid: **60'287** (40%)
    - credit collection: **59'013** (39%)
    - dismissed: **2'577** (1.7%)
    - paid & collection: 2 · paid & dismissed: 3 · collection & dismissed: 10 · all three: 0
    - **no outcome: 28'508** (19%)

    Pretty close to the hypothesis, except "paid" is lower than I thought and "no outcome" is bigger. Overlaps are almost zero, so the outcomes work as (more or less) separate endings.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **b) One case per outcome**
    """)
    return


@app.cell
def _(show_case, show_cols):
    out_cols = show_cols + ['outstanding_amount']
    show_case('A10000', out_cols)
    return (out_cols,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Paid – A10000:* standard parking fine, didn't pay within 60 days → penalty → then paid all 87 € about a year later. So "paid", but late and twice the price.
    """)
    return


@app.cell
def _(out_cols, show_case):
    show_case('A100', out_cols)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Credit collection – A100* (same case as in 2.3): never paid anything, penalty, two years later collection with 82.50 € open.
    """)
    return


@app.cell
def _(out_cols, show_case):
    show_case('A10001', out_cols)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Dismissed A10001:* the offender appealed to the prefecture shortly after the notification. Funny detail: the penalty is still added before the appeal is even sent (one day before). Then *Send Appeal to Prefecture* comes with `dismissal = #` → I read this as "dismissed by the prefecture". After that nothing happens anymore, no payment, no collection. So the penalty was added for nothing.
    **Finding:** the penalty should be paused while an appeal is open.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **c) Cases with more than one outcome**
    """)
    return


@app.cell
def _(out_cols, show_case):
    show_case('N35881', out_cols)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Paid + credit collection N35881:* the appeal was rejected (NIL), penalty was added, and the offender paid **79.30** on 9.5.2002 (owed 79.03, so even 27 cents too much). Still, almost **2 years later** the case is sent to credit collection.
    That looks like a real process error: somebody gets sent to the collection agency even though they paid. Maybe the payment was never matched to the fine.
    """)
    return


@app.cell
def _(out_cols, show_case):
    show_case('S188064', out_cols)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Paid + dismissed S188064:* appeal sent with `#`, but the person still pays the full 174 € including penalty afterwards. So either `#` doesn't really mean "dismissed" or the person paid anyway to be safe.
    I'm not sure anymore what `#` means.  "dismissed" outcome might be too broad.
    """)
    return


@app.cell
def _(out_cols, show_case):
    show_case('N21856', out_cols)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Credit collection + dismissed – N21856:* `dismissal = @` already at Create Fine, but then the normal process runs anyway, penalty and credit collection. So these other codes at creation (@, A, T, D, …) probably don't mean "dismissed" at all.
    The dismissal codes are not documented.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **d) Cases without outcome**
    """)
    return


@app.cell
def _(case_log, outcomes):
    no_outcome = case_log[~case_log[outcomes].any(axis=1)]
    print('only Create Fine + Send Fine:', ((no_outcome['no_of_events'] == 2) & (no_outcome['Send Fine'] == 1)).sum())
    print('partially paid:              ', (no_outcome['total_paid'] > 0).sum())
    print('with appeal to prefecture:   ', (no_outcome['Send Appeal to Prefecture'] > 0).sum())
    no_outcome['no_of_events'].value_counts().head()
    return


@app.cell
def _(out_cols, show_case):
    show_case('A1', out_cols)
    return


@app.cell
def _(out_cols, show_case):
    show_case('A10018', out_cols)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Two typical types:

    *A1:* Create Fine + Send Fine, then **nothing** anymore. Almost 20k cases (!) look like this, spread over all years, so it's not only "still running". Maybe the letter never arrived (no notification) and the fine expired, or the payment simply isn't in the log. Hard to say from the data.

    *A10018:* paid 35 € on the same day the penalty was added. The fine (22) + postage (13) = 35, so the person paid exactly the original amount, but the penalty came on that same day and now 22 € are "open" forever.
    Because of the day granularity we don't even know if the payment came before or after the penalty. If it came before, the penalty was probably wrong.

    Cases that just stop without any closing event should get an explicit end (e.g. "expired", "closed").
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Findings & open questions (so far)

    **Findings (process / data collection)**
    1. Timestamps only by day → record time or sequence numbers.
    2. Payments and totalPaymentAmount don't always match (double counted or lost payments) → give each payment a unique ID.
    3. Penalty is added even when an appeal is pending → pause the deadline during appeals.
    4. A case that was fully paid was still sent to credit collection → check payments before escalating.
    5. Dismissal codes are undocumented, and only partly mean "dismissed".
    6. ~20k cases end after Send Fine without any explanation → explicit closing event.
    7. `matricola` is always 0 and `lastSent` is missing in 1'631 notifications.

    **Open questions**
    - What do the dismissal codes (#, @, A, T, …) mean?
    - Why do only some fines of the same article get points?
    - Where do the negative outstanding amounts come from?
    - What happened to the cases that end after Send Fine?
    """)
    return


if __name__ == "__main__":
    app.run()
