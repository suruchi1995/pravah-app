"""
Forecasting engine — 5 models, auto-select by backtested MAPE.

Models: Moving Average (MA), Weighted MA (WMA), Single Exponential Smoothing (SES),
        Holt-Winters (additive trend+seasonal), Linear Regression (trend).

Method: per (item, location) monthly series, hold out the last HOLDOUT months,
fit each model on the rest, forecast the holdout, score MAPE + bias. Pick the
lowest-MAPE model, refit on the full series, and project HORIZON months forward.

Pure-Python/numpy implementations (no statsmodels dependency) so it runs anywhere
and is fully transparent. Writes forecast_output with selected model + metrics + reasoning.
"""
import os, sys, math
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT

HOLDOUT = 3       # months held out for backtest
HORIZON = 6       # months to forecast forward
SEASON = 12       # seasonal period


def _next_periods(last_period, n):
    y, mo = int(last_period[:4]), int(last_period[5:7])
    out = []
    for _ in range(n):
        mo += 1
        if mo > 12:
            mo = 1; y += 1
        out.append(f"{y:04d}-{mo:02d}-01")
    return out


# ---- models: each takes a train list, returns a function f(h) -> forecast for step h (1-based) ----
def fit_ma(train, window=3):
    w = train[-window:] if len(train) >= window else train
    val = sum(w) / len(w)
    return lambda h: val

def fit_wma(train, window=3):
    w = train[-window:] if len(train) >= window else train
    weights = list(range(1, len(w) + 1))
    val = sum(x * wt for x, wt in zip(w, weights)) / sum(weights)
    return lambda h: val

def fit_ses(train, alpha=0.4):
    level = train[0]
    for x in train[1:]:
        level = alpha * x + (1 - alpha) * level
    return lambda h: level

def fit_linreg(train):
    n = len(train)
    xs = list(range(n))
    mx = sum(xs) / n; my = sum(train) / n
    denom = sum((x - mx) ** 2 for x in xs) or 1e-9
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, train)) / denom
    intercept = my - slope * mx
    return lambda h: max(0.0, intercept + slope * (n - 1 + h))

def fit_holt_winters(train, alpha=0.3, beta=0.1, gamma=0.2, season=SEASON):
    if len(train) < season + 2:
        # not enough data for seasonality -> fall back to linear-ish SES
        return fit_ses(train)
    # initial level/trend/seasonals
    seasons = train[:season]
    level = sum(seasons) / season
    trend = (sum(train[season:2*season]) - sum(train[:season])) / (season * season) \
        if len(train) >= 2*season else 0.0
    seasonal = [train[i] - level for i in range(season)]
    for t in range(season, len(train)):
        prev_level = level
        s = seasonal[t % season]
        level = alpha * (train[t] - s) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        seasonal[t % season] = gamma * (train[t] - level) + (1 - gamma) * s
    def f(h):
        return max(0.0, level + h * trend + seasonal[(len(train) - 1 + h) % season])
    return f

MODELS = {
    "MovingAverage": fit_ma,
    "WeightedMA": fit_wma,
    "SES": fit_ses,
    "HoltWinters": fit_holt_winters,
    "LinearRegression": fit_linreg,
}


def _mape_bias(actual, predicted):
    errs, biases = [], []
    for a, p in zip(actual, predicted):
        if a != 0:
            errs.append(abs(a - p) / abs(a))
        biases.append(p - a)
    mape = (sum(errs) / len(errs) * 100) if errs else 0.0
    bias = sum(biases) / len(biases) if biases else 0.0
    return mape, bias


def run(session, tenant=DEFAULT_TENANT):
    from backend.parameters import get_param
    HOLDOUT = get_param(session, "forecast_holdout_months", tenant)
    HORIZON = get_param(session, "forecast_horizon_months", tenant)
    SEASON_P = get_param(session, "forecast_season_length", tenant)
    ses_a = get_param(session, "ses_alpha", tenant)
    hw_a = get_param(session, "hw_alpha", tenant)
    hw_b = get_param(session, "hw_beta", tenant)
    hw_g = get_param(session, "hw_gamma", tenant)

    # parameterised model set (reads tunables from the registry, nothing hardcoded)
    models = {
        "MovingAverage":     lambda tr: fit_ma(tr),
        "WeightedMA":        lambda tr: fit_wma(tr),
        "SES":               lambda tr: fit_ses(tr, alpha=ses_a),
        "HoltWinters":       lambda tr: fit_holt_winters(tr, alpha=hw_a, beta=hw_b, gamma=hw_g, season=SEASON_P),
        "LinearRegression":  lambda tr: fit_linreg(tr),
    }

    # build (item, loc) -> ordered monthly series
    series = defaultdict(dict)
    for d in session.query(m.DemandHistory).filter_by(tenant_id=tenant):
        series[(d.item_code, d.location_code)][d.period] = d.quantity

    session.query(m.ForecastOutput).filter_by(tenant_id=tenant).delete()
    out_rows = []
    for (item, loc), pmap in series.items():
        periods = sorted(pmap)
        values = [pmap[p] for p in periods]
        if len(values) < HOLDOUT + 3:
            continue
        train, test = values[:-HOLDOUT], values[-HOLDOUT:]

        scores = {}
        for name, fitter in models.items():
            f = fitter(train)
            preds = [f(h) for h in range(1, HOLDOUT + 1)]
            mape, bias = _mape_bias(test, preds)
            scores[name] = (mape, bias)

        best = min(scores, key=lambda k: scores[k][0])
        best_mape, best_bias = scores[best]

        f_full = models[best](values)
        fut_periods = _next_periods(periods[-1], HORIZON)
        ranked = sorted(scores.items(), key=lambda kv: kv[1][0])
        runner = ranked[1][0] if len(ranked) > 1 else best
        reason = (f"Backtest on last {HOLDOUT} months: {best} won with MAPE={best_mape:.1f}% "
                  f"(next best {runner} {scores[runner][0]:.1f}%). Bias={best_bias:+.1f}.")
        for h, p in enumerate(fut_periods, start=1):
            out_rows.append(m.ForecastOutput(
                tenant_id=tenant, item_code=item, location_code=loc, period=p,
                forecast_qty=round(f_full(h), 2), selected_model=best,
                mape=round(best_mape, 2), bias=round(best_bias, 2), reasoning=reason))
    session.bulk_save_objects(out_rows)
    session.commit()
    return len(out_rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); m.init_db(eng)
    Session = m.make_session_factory(eng)
    with Session() as ssn:
        n = run(ssn)
        print(f"Forecast rows written: {n}")
        # model selection summary
        from collections import Counter
        rows = ssn.query(m.ForecastOutput).filter_by(tenant_id="apex").all()
        chosen = Counter((r.item_code, r.location_code, r.selected_model) for r in rows)
        by_model = Counter(k[2] for k in chosen)
        print("Model chosen across", len(chosen), "series:", dict(by_model))
        avg_mape = sum(r.mape for r in rows)/len(rows)
        print(f"Avg MAPE across all forecast rows: {avg_mape:.1f}%")
        # show FG001 / DC_DEL
        print("\nFG001 @ DC_DEL forecast:")
        for r in ssn.query(m.ForecastOutput).filter_by(tenant_id="apex", item_code="FG001", location_code="DC_DEL").order_by(m.ForecastOutput.period):
            print(f"  {r.period}  qty={r.forecast_qty:>8.0f}  [{r.selected_model}, MAPE {r.mape:.1f}%]")
