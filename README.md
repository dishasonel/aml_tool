# 🕵️ AML Detection

An **Anti-Money Laundering (AML) detection system** that combines:
- 📊 Interactive **dashboard** (HTML/JS frontend)
- 🧠 **Machine learning (Isolation Forest)** for anomaly detection
- 🔗 **Graph-based analysis** for cycles and fan-in/out detection
- 📑 Export options (CSV/PDF)
- 👤 Authentication & Multi-region **admin login**

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

## 📝 License

This project is developed **for educational and hackathon purposes only**.  
It is not intended for production or commercial deployment.  
You are free to use, modify, and share it for **learning, research, or demo projects**.

