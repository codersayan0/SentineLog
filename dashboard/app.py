import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "https://sentinelog.onrender.com")

st.set_page_config(
    page_title="SentinelLog",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
    .main { padding: 1rem 2rem; }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #378ADD;
    }
    .critical { border-left-color: #E24B4A !important; }
    .high     { border-left-color: #EF9F27 !important; }
    .medium   { border-left-color: #378ADD !important; }
    .low      { border-left-color: #1D9E75 !important; }
    .badge-critical { background:#FCEBEB; color:#A32D2D; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:500; }
    .badge-high     { background:#FAEEDA; color:#633806; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:500; }
    .badge-medium   { background:#E6F1FB; color:#0C447C; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:500; }
    .badge-low      { background:#E1F5EE; color:#085041; padding:3px 10px; border-radius:99px; font-size:12px; font-weight:500; }
    .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)


# ── Helper functions ──────────────────────────────────────

def fetch_stats():
    try:
        r = requests.get(f"{BACKEND_URL}/stats", timeout=5)
        return r.json()
    except:
        return {"total_alerts": 0, "critical": 0, "high": 0,
                "medium": 0, "low": 0, "unique_ips_flagged": 0}

def fetch_alerts(limit=100, severity=None):
    try:
        params = {"limit": limit}
        if severity and severity != "All":
            params["severity"] = severity.lower()
        r = requests.get(f"{BACKEND_URL}/alerts", params=params, timeout=5)
        data = r.json()
        return pd.DataFrame(data.get("alerts", []))
    except:
        return pd.DataFrame()

def fetch_logs(limit=200):
    try:
        r = requests.get(f"{BACKEND_URL}/logs", params={"limit": limit}, timeout=5)
        data = r.json()
        return pd.DataFrame(data.get("logs", []))
    except:
        return pd.DataFrame()

def trigger_analysis():
    try:
        r = requests.post(f"{BACKEND_URL}/analyze", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def severity_badge(severity: str) -> str:
    s = severity.lower()
    return f'<span class="badge-{s}">{s.upper()}</span>'

def severity_color(severity: str) -> str:
    colors = {
        "critical": "#E24B4A",
        "high": "#EF9F27",
        "medium": "#378ADD",
        "low": "#1D9E75",
    }
    return colors.get(severity.lower(), "#888780")


# ── Sidebar ───────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛡️ SentinelLog")
    st.markdown("*AI-Powered Threat Monitor*")
    st.divider()

    st.markdown("### Controls")

    if st.button("🔍 Run Analysis Now", use_container_width=True):
        with st.spinner("Analyzing logs..."):
            result = trigger_analysis()
            st.success("Analysis triggered! Refresh in 10 seconds.")

    auto_refresh = st.toggle("Auto refresh (30s)", value=False)

    st.divider()
    st.markdown("### Filters")

    severity_filter = st.selectbox(
        "Severity",
        ["All", "Critical", "High", "Medium", "Low"]
    )

    alert_limit = st.slider("Max alerts to show", 10, 200, 50, step=10)

    st.divider()
    st.markdown("### Pages")
    page = st.radio(
        "Navigate",
        ["Dashboard", "Alert Feed", "Raw Logs", "Analytics"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption(f"Backend: `{BACKEND_URL}`")
    st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")


# ── Auto refresh ──────────────────────────────────────────
if auto_refresh:
    time.sleep(30)
    st.rerun()


# ══════════════════════════════════════════════════════════
# PAGE 1 — Dashboard
# ══════════════════════════════════════════════════════════

if page == "Dashboard":
    st.title("🛡️ SentinelLog — Live Threat Monitor")
    st.caption("Real-time log anomaly detection powered by ML + LLM")
    st.divider()

    # ── Metric cards
    stats = fetch_stats()
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("Total Alerts",    stats.get("total_alerts", 0))
    c2.metric("🔴 Critical",     stats.get("critical", 0))
    c3.metric("🟠 High",         stats.get("high", 0))
    c4.metric("🔵 Medium",       stats.get("medium", 0))
    c5.metric("🟢 Low",          stats.get("low", 0))
    c6.metric("IPs Flagged",     stats.get("unique_ips_flagged", 0))

    st.divider()

    # ── Charts row
    alerts_df = fetch_alerts(limit=200)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("#### Severity Breakdown")
        if not alerts_df.empty and "severity" in alerts_df.columns:
            sev_counts = alerts_df["severity"].value_counts().reset_index()
            sev_counts.columns = ["severity", "count"]
            color_map = {
                "critical": "#E24B4A",
                "high": "#EF9F27",
                "medium": "#378ADD",
                "low": "#1D9E75"
            }
            fig = px.pie(
                sev_counts,
                names="severity",
                values="count",
                color="severity",
                color_discrete_map=color_map,
                hole=0.5,
            )
            fig.update_traces(textposition="outside", textinfo="percent+label")
            fig.update_layout(
                showlegend=False,
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No alert data yet. Run analysis first.")

    with col_right:
        st.markdown("#### Threat Types Detected")
        if not alerts_df.empty and "threat_type" in alerts_df.columns:
            threat_counts = alerts_df["threat_type"].value_counts().reset_index()
            threat_counts.columns = ["threat_type", "count"]
            fig2 = px.bar(
                threat_counts,
                x="count",
                y="threat_type",
                orientation="h",
                color="count",
                color_continuous_scale=["#E6F1FB", "#378ADD", "#0C447C"],
            )
            fig2.update_layout(
                showlegend=False,
                coloraxis_showscale=False,
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
                yaxis_title="",
                xaxis_title="Count",
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No threat data yet.")

    st.divider()

    # ── Top attacker IPs
    st.markdown("#### Top Flagged IPs")
    if not alerts_df.empty and "ip" in alerts_df.columns:
        top_ips = alerts_df["ip"].value_counts().head(10).reset_index()
        top_ips.columns = ["ip", "alert_count"]
        fig3 = px.bar(
            top_ips,
            x="alert_count",
            y="ip",
            orientation="h",
            color="alert_count",
            color_continuous_scale=["#FAEEDA", "#EF9F27", "#633806"],
        )
        fig3.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
            yaxis_title="",
            xaxis_title="Number of Alerts",
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No IP data yet.")

    st.divider()

    # ── Recent critical alerts preview
    st.markdown("#### Recent Critical Alerts")
    if not alerts_df.empty:
        critical_df = alerts_df[alerts_df["severity"] == "critical"].head(5)
        if not critical_df.empty:
            for _, row in critical_df.iterrows():
                with st.expander(
                    f"🔴 {row.get('ip', 'N/A')} — {row.get('threat_type', 'unknown').replace('_', ' ').title()} "
                    f"| Score: {row.get('anomaly_score', 0):.0f}/100"
                ):
                    st.markdown(f"**Explanation:** {row.get('explanation', 'N/A')}")
                    st.markdown(f"**Remediation:** {row.get('remediation', 'N/A')}")
                    st.code(row.get("raw_log", ""), language="text")
        else:
            st.success("No critical alerts — system looks healthy.")
    else:
        st.info("Run analysis to see alerts here.")


# ══════════════════════════════════════════════════════════
# PAGE 2 — Alert Feed
# ══════════════════════════════════════════════════════════

elif page == "Alert Feed":
    st.title("📋 Alert Feed")
    st.caption("All flagged log entries with AI-generated threat explanations")
    st.divider()

    alerts_df = fetch_alerts(limit=alert_limit, severity=severity_filter)

    if alerts_df.empty:
        st.warning("No alerts found. Run analysis from the sidebar.")
    else:
        st.markdown(f"Showing **{len(alerts_df)}** alerts")

        for _, row in alerts_df.iterrows():
            sev = row.get("severity", "low").lower()
            color = severity_color(sev)
            score = row.get("anomaly_score", 0)
            threat = row.get("threat_type", "unknown").replace("_", " ").title()
            ip = row.get("ip", "N/A")
            ts = row.get("timestamp", "N/A")

            with st.expander(
                f"{'🔴' if sev == 'critical' else '🟠' if sev == 'high' else '🔵' if sev == 'medium' else '🟢'} "
                f"[{sev.upper()}] {ip} — {threat} | Score: {score:.0f}/100 | {ts}"
            ):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("**Threat Details**")
                    st.markdown(f"- **IP Address:** `{ip}`")
                    st.markdown(f"- **Threat Type:** {threat}")
                    st.markdown(f"- **Severity:** {sev.upper()}")
                    st.markdown(f"- **Anomaly Score:** {score:.1f} / 100")
                    st.markdown(f"- **Timestamp:** {ts}")

                with col2:
                    st.markdown("**AI Analysis**")
                    st.info(f"📝 {row.get('explanation', 'N/A')}")
                    st.warning(f"⚡ **Action:** {row.get('remediation', 'N/A')}")

                st.markdown("**Raw Log Entry**")
                st.code(row.get("raw_log", "N/A"), language="text")


# ══════════════════════════════════════════════════════════
# PAGE 3 — Raw Logs
# ══════════════════════════════════════════════════════════

elif page == "Raw Logs":
    st.title("📄 Raw Log Viewer")
    st.caption("Live view of incoming server logs")
    st.divider()

    logs_df = fetch_logs(limit=500)

    if logs_df.empty:
        st.warning("No logs found. Make sure the backend is running and logs are generated.")
    else:
        # Summary row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Entries", len(logs_df))

        if "status_code" in logs_df.columns:
            errors = logs_df[logs_df["status_code"] >= 400]
            col2.metric("Error Responses", len(errors))
            col3.metric("Error Rate", f"{len(errors)/len(logs_df)*100:.1f}%")

        if "response_time" in logs_df.columns:
            col4.metric("Avg Response Time", f"{logs_df['response_time'].mean():.3f}s")

        st.divider()

        # Search/filter
        search = st.text_input("Search logs by IP, endpoint, or status", placeholder="e.g. 192.168 or /admin or 404")
        if search:
            mask = logs_df.astype(str).apply(lambda row: row.str.contains(search, case=False).any(), axis=1)
            logs_df = logs_df[mask]
            st.caption(f"{len(logs_df)} entries match '{search}'")

        # Color-code by status
        def highlight_status(val):
            if isinstance(val, int):
                if val >= 500:
                    return "background-color: #FCEBEB; color: #A32D2D"
                elif val >= 400:
                    return "background-color: #FAEEDA; color: #633806"
                elif val >= 300:
                    return "background-color: #E6F1FB; color: #0C447C"
            return ""

        display_cols = [c for c in ["timestamp", "ip", "method", "endpoint",
                                     "status_code", "response_time", "payload_size"]
                        if c in logs_df.columns]

        styled = logs_df[display_cols].head(200).style.applymap(
            highlight_status, subset=["status_code"] if "status_code" in display_cols else []
        )
        st.dataframe(styled, use_container_width=True, height=500)


# ══════════════════════════════════════════════════════════
# PAGE 4 — Analytics
# ══════════════════════════════════════════════════════════

elif page == "Analytics":
    st.title("📊 Analytics")
    st.caption("Deep-dive into threat patterns and system behavior")
    st.divider()

    alerts_df = fetch_alerts(limit=500)
    logs_df   = fetch_logs(limit=1000)

    if alerts_df.empty:
        st.warning("No alert data available. Run analysis first.")
    else:

        # ── Anomaly score distribution
        st.markdown("#### Anomaly Score Distribution")
        if "anomaly_score" in alerts_df.columns:
            fig = px.histogram(
                alerts_df,
                x="anomaly_score",
                nbins=30,
                color_discrete_sequence=["#378ADD"],
                labels={"anomaly_score": "Anomaly Score (0–100)"},
            )
            fig.add_vline(x=70, line_dash="dash", line_color="#E24B4A",
                          annotation_text="High risk threshold")
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=280,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        col1, col2 = st.columns(2)

        # ── Severity over time
        with col1:
            st.markdown("#### Alerts by Severity Over Time")
            if "timestamp" in alerts_df.columns and "severity" in alerts_df.columns:
                alerts_df["hour"] = pd.to_datetime(
                    alerts_df["timestamp"], format="%d/%b/%Y:%H:%M:%S +0000", errors="coerce"
                ).dt.floor("H")

                time_sev = alerts_df.groupby(["hour", "severity"]).size().reset_index(name="count")
                time_sev = time_sev.dropna(subset=["hour"])

                color_map = {
                    "critical": "#E24B4A",
                    "high": "#EF9F27",
                    "medium": "#378ADD",
                    "low": "#1D9E75",
                }
                fig4 = px.bar(
                    time_sev,
                    x="hour",
                    y="count",
                    color="severity",
                    color_discrete_map=color_map,
                    barmode="stack",
                )
                fig4.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=280,
                    xaxis_title="",
                    yaxis_title="Alert Count",
                    legend_title="Severity",
                )
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Not enough timestamp data.")

        # ── Response time vs anomaly score scatter
        with col2:
            st.markdown("#### Response Time vs Anomaly Score")
            if not logs_df.empty and not alerts_df.empty:
                if "response_time" in alerts_df.columns and "anomaly_score" in alerts_df.columns:
                    fig5 = px.scatter(
                        alerts_df,
                        x="response_time",
                        y="anomaly_score",
                        color="severity",
                        color_discrete_map={
                            "critical": "#E24B4A",
                            "high": "#EF9F27",
                            "medium": "#378ADD",
                            "low": "#1D9E75",
                        },
                        hover_data=["ip", "threat_type"],
                        labels={
                            "response_time": "Response Time (s)",
                            "anomaly_score": "Anomaly Score",
                        },
                    )
                    fig5.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=280,
                    )
                    st.plotly_chart(fig5, use_container_width=True)
                else:
                    st.info("Not enough feature data.")
            else:
                st.info("No data available.")

        st.divider()

        # ── IP attack frequency table
        st.markdown("#### IP Attack Frequency Table")
        if "ip" in alerts_df.columns and "severity" in alerts_df.columns:
            ip_summary = alerts_df.groupby("ip").agg(
                total_alerts=("ip", "count"),
                critical=("severity", lambda x: (x == "critical").sum()),
                high=("severity", lambda x: (x == "high").sum()),
                avg_score=("anomaly_score", "mean"),
                threat_types=("threat_type", lambda x: ", ".join(x.unique())),
            ).reset_index().sort_values("total_alerts", ascending=False)

            ip_summary["avg_score"] = ip_summary["avg_score"].round(1)

            st.dataframe(
                ip_summary.head(20),
                use_container_width=True,
                column_config={
                    "ip": "IP Address",
                    "total_alerts": st.column_config.NumberColumn("Total Alerts", format="%d"),
                    "critical": st.column_config.NumberColumn("Critical", format="%d"),
                    "high": st.column_config.NumberColumn("High", format="%d"),
                    "avg_score": st.column_config.NumberColumn("Avg Score", format="%.1f"),
                    "threat_types": "Threat Types",
                }
            )

        st.divider()

        # ── Error rate over time from raw logs
        st.markdown("#### Error Rate Over Time (Raw Logs)")
        if not logs_df.empty and "status_code" in logs_df.columns:
            logs_df["is_error"] = logs_df["status_code"] >= 400
            logs_df["parsed_time"] = pd.to_datetime(
                logs_df["timestamp"], format="%d/%b/%Y:%H:%M:%S +0000", errors="coerce"
            ).dt.floor("10min")

            error_over_time = logs_df.groupby("parsed_time").agg(
                error_rate=("is_error", "mean"),
                total=("is_error", "count"),
            ).reset_index().dropna(subset=["parsed_time"])

            fig6 = px.line(
                error_over_time,
                x="parsed_time",
                y="error_rate",
                labels={"parsed_time": "", "error_rate": "Error Rate"},
                color_discrete_sequence=["#E24B4A"],
            )
            fig6.add_hline(y=0.3, line_dash="dash", line_color="#EF9F27",
                           annotation_text="Warning threshold (30%)")
            fig6.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=260,
                yaxis_tickformat=".0%",
            )
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("No raw log data available.")