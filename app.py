from flask import Flask, render_template, request, redirect, url_for, session
import os
import pandas as pd
import networkx as nx
from sklearn.ensemble import IsolationForest

app = Flask(__name__)
app.secret_key = "supersecretkey"  # replace in production
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------
# Region-scoped admins
# -------------------
USERS = {
    "admin_indore": {"password": "1234", "region": "Indore"},
    "admin_bhopal": {"password": "5678", "region": "Bhopal"},
    "admin_dewas":  {"password": "9999", "region": "Dewas"},
}

# -------------------
# Flexible CSV header handling
# -------------------
def _canon(s: str) -> str:
    return "".join(ch for ch in s.lower().strip() if ch.isalnum())

def _pick(df, name_variants=None, regex_parts=None, prefer_numeric=False):
    """Pick the best-matching column from df."""
    cols = list(df.columns)
    canon_map = {c: _canon(c) for c in cols}

    # 1) direct variants match
    if name_variants:
        targets = {_canon(v) for v in name_variants}
        for c in cols:
            if canon_map[c] in targets:
                return c

    # 2) regex-like contains (any part contained in canon name)
    if regex_parts:
        parts = [_canon(p) for p in regex_parts]
        # score by number of matching parts
        best = None
        best_score = -1
        for c in cols:
            score = sum(1 for p in parts if p in canon_map[c])
            if score > best_score:
                best, best_score = c, score
        # need at least one part match
        if best_score > 0:
            return best

    # 3) fallback numeric heuristic if needed
    if prefer_numeric:
        numeric_candidates = []
        for c in cols:
            ser = pd.to_numeric(df[c], errors="coerce")
            pct_numeric = ser.notna().mean()
            if pct_numeric >= 0.8:  # mostly numeric
                numeric_candidates.append((pct_numeric, c))
        if numeric_candidates:
            numeric_candidates.sort(reverse=True)
            return numeric_candidates[0][1]

    return None

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Strip whitespace from headers
    df = df.rename(columns={c: c.strip() for c in df.columns})

    # ----- Detect required columns -----
    col_id = _pick(
        df,
        name_variants=["transaction_id", "txn_id", "txnid", "id"],
        regex_parts=["transaction id", "txn", "tx id", "unique id"]
    )
    col_src = _pick(
        df,
        name_variants=["src", "source", "from", "from_account", "sender", "originator", "debitedby"],
        regex_parts=["sender", "payer", "from", "src", "debit", "customerfrom", "accountfrom", "sendername"]
    )
    col_dst = _pick(
        df,
        name_variants=["dst", "destination", "to", "to_account", "receiver", "beneficiary", "creditedto"],
        regex_parts=["receiver", "payee", "to", "dst", "credit", "customerto", "accountto", "receivername"]
    )
    col_amount = _pick(
        df,
        name_variants=["amount", "amt", "value", "amount_usd", "amountinr", "transactionamount"],
        regex_parts=["amount", "value", "amt", "sum", "transfer"],
        prefer_numeric=True
    )
    col_type = _pick(
        df,
        name_variants=["type", "transaction_type", "transactiontype", "mode", "method", "category", "channel"],
        regex_parts=["type", "mode", "method", "category", "channel"]
    )
    col_loc = _pick(
        df,
        name_variants=["location", "branch", "origin", "region", "city"],
        regex_parts=["location", "branch", "region", "city", "country"]
    )

    # Rename the ones we found to canonical names
    rename = {}
    if col_id:     rename[col_id] = "transaction_id"
    if col_src:    rename[col_src] = "src"
    if col_dst:    rename[col_dst] = "dst"
    if col_amount: rename[col_amount] = "amount"
    if col_type:   rename[col_type] = "type"
    if col_loc:    rename[col_loc] = "location"
    df = df.rename(columns=rename)

    required = {"transaction_id", "src", "dst", "amount", "type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV must contain columns: {sorted(list(required))}. Missing: {sorted(list(missing))}"
        )

    return df

# -------------------
# ML & Graph logic
# -------------------
def run_ml_model(transactions: pd.DataFrame) -> pd.DataFrame:
    x = pd.to_numeric(transactions["amount"], errors="coerce").fillna(0).values.reshape(-1, 1)
    try:
        model = IsolationForest(contamination=0.1, random_state=42)
        pred = model.fit_predict(x)
        transactions["ml_anomaly"] = (pred == -1)
    except Exception:
        transactions["ml_anomaly"] = False
    return transactions

def detect_patterns(transactions: pd.DataFrame):
    MG = nx.MultiDiGraph()
    for _, r in transactions.iterrows():
        MG.add_edge(
            str(r["src"]), str(r["dst"]),
            key=str(r["transaction_id"]),
            txn_id=str(r["transaction_id"]),
            amount=float(pd.to_numeric(r["amount"], errors="coerce") or 0.0)
        )

    patterns_by_txn = {}
    # Fan-in / Fan-out
    for n in MG.nodes():
        if MG.out_degree(n) > 3:
            for _, _, _, data in MG.out_edges(n, keys=True, data=True):
                patterns_by_txn[data["txn_id"]] = "Fan-out pattern"
        if MG.in_degree(n) > 3:
            for _, _, _, data in MG.in_edges(n, keys=True, data=True):
                patterns_by_txn[data["txn_id"]] = "Fan-in pattern"

    # Cycles (any length >=2)
    DG = nx.DiGraph()
    for u, v in MG.edges():
        DG.add_edge(u, v)

    cycles_nodes = []
    cycle_txn_ids = set()
    try:
        for cyc in nx.simple_cycles(DG):
            if len(cyc) >= 2:
                cycles_nodes.append(cyc[:])
                for i in range(len(cyc)):
                    u, v = cyc[i], cyc[(i + 1) % len(cyc)]
                    if MG.has_edge(u, v):
                        for _, _, data in MG.edges(u, v, data=True):
                            cycle_txn_ids.add(data["txn_id"])
                            patterns_by_txn[data["txn_id"]] = "Cycle detected"
    except Exception:
        pass

    return patterns_by_txn, cycles_nodes, cycle_txn_ids

# -------------------
# Routes
# -------------------
@app.route("/")
def login_page():
    return render_template("index3.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    region   = request.form.get("region", "").strip()
    user = USERS.get(username)
    if user and user["password"] == password and user["region"] == region:
        session["user"] = username
        session["region"] = region
        return redirect(url_for("dashboard"))
    return render_template("index3.html", error="Invalid credentials")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("dashboard.html", region=session["region"], user=session["user"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return "Unauthorized. Please login first.", 401
    if "file" not in request.files:
        return "No file uploaded", 400

    f = request.files["file"]
    if not f.filename:
        return "No file selected", 400

    fp = os.path.join(UPLOAD_FOLDER, f.filename)
    f.save(fp)

    # Robust CSV read: auto delimiter, handles BOM/TSV/semicolon
    try:
        df = pd.read_csv(fp, sep=None, engine="python", dtype=str)
    except Exception:
        # Fallback to default comma
        try:
            df = pd.read_csv(fp, dtype=str)
        except Exception as e2:
            return f"CSV read/format error: {e2}", 400

    try:
        df = normalize_columns(df)
    except ValueError as ve:
        return str(ve), 400

    # Clean
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    # ML & graph
    df = run_ml_model(df)
    patterns, cycles_nodes, cycle_txn_ids = detect_patterns(df)

    rows = []
    for _, r in df.iterrows():
        reasons, risk = [], 0.0
        amt = float(r["amount"])
        ttype = str(r["type"]).lower()
        txn_id = str(r["transaction_id"])

        if amt > 400000:
            risk += 0.5; reasons.append("High transaction amount")
        if ttype in ["cash", "crypto", "offshore", "shell"]:
            risk += 0.2; reasons.append("Suspicious transaction type")
        if bool(r.get("ml_anomaly", False)):
            risk += 0.6; reasons.append("ML anomaly detected")
        if txn_id in patterns:
            risk += 0.4; reasons.append(patterns[txn_id])

        suspicious = int(
            risk >= 0.9 or
            (amt > 500000 and bool(r.get("ml_anomaly", False))) or
            (bool(r.get("ml_anomaly", False)) and txn_id in patterns) or
            (txn_id in cycle_txn_ids and amt > 400000)
        )

        rows.append({
            "id": txn_id,
            "src": str(r["src"]),
            "dst": str(r["dst"]),
            "amount": amt,
            "type": str(r["type"]),
            "location": str(r.get("location", "N/A")),
            "risk": round(risk, 2),
            "susp": suspicious,
            "in_cycle": int(txn_id in cycle_txn_ids),
            "reasons": "; ".join(reasons) if reasons else "No strong red flags",
        })

    # Flask auto-serializes dicts to JSON
    return {"rows": rows, "cycles": cycles_nodes}

if __name__ == "__main__":
    app.run(debug=True)

