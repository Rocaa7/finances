"""Llegeix isins.txt, busca el preu actual de cada ISIN a Yahoo i l'escriu en EUR a prices.json.
Criptos de Trade Republic (ISIN tipus XF000BTC0017) -> BTC-EUR.  Només stdlib."""
import json, re, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
PREFER = (".DE", ".F", ".AS", ".PA", ".MI", ".MC", ".VI", ".BR")  # borses en EUR primer


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return json.load(r)


def chart(symbol, rng="1d", interval="1d"):
    return get(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range={rng}&interval={interval}")["chart"]["result"][0]


def quote(symbol):
    m = chart(symbol)["meta"]
    return m["regularMarketPrice"], m["currency"]


def monthly(symbol):
    """Tancament de cada mes dels últims 2 anys: ({'2026-10': preu, ...}, moneda)."""
    r = chart(symbol, "2y", "1mo")
    closes = r["indicators"]["quote"][0]["close"]
    # +3 dies: el timestamp és l'inici del mes en hora local de la borsa
    return {time.strftime("%Y-%m", time.gmtime(t + 3 * 86400)): c for t, c in zip(r.get("timestamp", []), closes) if c}, r["meta"]["currency"]


def hist_eur(symbol, fxh={}):
    h, cur = monthly(symbol)
    if cur == "GBp":
        h, cur = {m: p / 100 for m, p in h.items()}, "GBP"
    if cur != "EUR":
        if cur not in fxh:
            fxh[cur] = monthly(f"EUR{cur}=X")[0]
        now = to_eur(1, cur)  # si falta el canvi d'un mes, el d'avui
        h = {m: p / fxh[cur][m] if m in fxh[cur] else p * now for m, p in h.items()}
    return {m: round(p, 4) for m, p in h.items()}


def to_eur(price, cur, fx={}):
    if cur == "GBp":
        price, cur = price / 100, "GBP"
    if cur == "EUR":
        return price
    if cur not in fx:
        fx[cur] = quote(f"EUR{cur}=X")[0]  # quantes unitats de cur val 1 EUR
    return price / fx[cur]


def symbols_for(isin):
    m = re.fullmatch(r"XF000([A-Z]+?)0\d+", isin) or re.fullmatch(r"([A-Z]{2,6})", isin)  # cripto: XF000BTC0017 o BTC
    if m:
        return [f"{m.group(1)}-EUR"]
    qs = get(f"https://query2.finance.yahoo.com/v1/finance/search?q={isin}&quotesCount=10&newsCount=0")["quotes"]
    syms = [q["symbol"] for q in qs if q.get("symbol")]
    return sorted(syms, key=lambda s: next((i for i, p in enumerate(PREFER) if s.endswith(p)), 99))


def price_for(isin):
    for s in symbols_for(isin)[:4]:
        try:
            p, cur = quote(s)
            r = {"eur": round(to_eur(p, cur), 4), "symbol": s}
            try:
                r["hist"] = hist_eur(s)  # per al gràfic d'evolució del patrimoni
            except Exception as e:
                print(s, "sense historic:", e, file=sys.stderr)
            return r
        except Exception:
            continue
    return None


def main(src="isins.txt", out="prices.json"):
    isins = sorted({l.split("#")[0].strip().upper() for l in open(src, encoding="utf-8")} - {""})
    prices, missing = {}, []
    for isin in isins:
        try:
            r = price_for(isin)
        except Exception as e:
            r = None
            print(isin, "error:", e, file=sys.stderr)
        if r:
            prices[isin] = r
        else:
            missing.append(isin)
        print(isin, r)
    json.dump({"updated": int(time.time()), "prices": prices, "missing": missing}, open(out, "w"), indent=1)


if __name__ == "__main__":
    assert re.fullmatch(r"XF000([A-Z]+?)0\d+", "XF000BTC0017").group(1) == "BTC"
    main(*sys.argv[1:])
