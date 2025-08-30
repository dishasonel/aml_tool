# 🕵️ AML Detection Dashboard

An **Anti-Money Laundering (AML) detection system** that combines:
- Admin Login System with region-based access (Indore, Bhopal, Dewas).
- CSV Upload & Analysis of transactions.
- Machine Learning (Isolation Forest) for anomaly detection.
- Graph Analysis to identify fan-in, fan-out, and cycle patterns.
- Interactive Dashboard with transaction graphs, scatter plots, and suspicious transaction tables.
- Alert System to notify users about risky activities.
---

## 🚀 Features

- Upload **CSV transaction files** (flexible header detection).
- Detects **suspicious transactions** based on:
  - High amounts
  - Suspicious transaction types (cash, crypto, offshore, shell)
  - ML anomalies (Isolation Forest)
  - Graph patterns (cycles, fan-in, fan-out)
- Interactive **transaction graph** (Cytoscape.js):
  - Nodes = Accounts
  - Edges = Transactions
  - Click nodes/edges to view details
- **Scatter plot** (Chart.js) for amounts
- **Suspicious transaction table** with search filter
- Popup with **export options**:
  - Download selected transactions as **CSV** or **PDF**
- Real-time **toast notifications** for alerts
- Region-specific **admin login system**

---

## 🛠️ Tech Stack

### Backend
- **Flask** (Python)
- **Pandas** (CSV parsing & preprocessing)
- **scikit-learn** (Isolation Forest anomaly detection)
- **NetworkX** (graph cycle & pattern detection)

### Frontend
- **HTML/CSS/JS**
- **Cytoscape.js** (graph visualization)
- **Chart.js** (scatter plots)
- **jsPDF & FileSaver.js** (report downloads)

---

## 📂 Project Structure

