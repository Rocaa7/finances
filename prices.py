"""Llegeix isins.txt, busca el preu actual de cada ISIN a Yahoo i l'escriu en EUR a prices.json.
Criptos de Trade Republic (ISIN tipus XF000BTC0017) -> BTC-EUR.  Només stdlib."""
import json, re, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
PREFER = (".DE", ".F", ".AS", ".PA", ".MI", ".MC", ".VI", ".BR")  # borses en EUR primer


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return json.load(r)


def quote(symbol):
    m = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range=1d&interval=1d")["chart"]["result"][0]["meta"]
    return m["regularMarketPrice"], m["currency"]


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
            return {"eur": round(to_eur(p, cur), 4), "symbol": s}
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
