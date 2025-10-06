#!/usr/bin/env python3
"""
Cloud SQL Tuning Agent - starter

Usage:
  export OPENAI_API_KEY="sk-..."
  python agent.py sample_inputs/metrics.json sample_inputs/db_flags.txt sample_inputs/slow_queries.log
"""

import sys
import json
import re
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import pandas as pd
from openai import OpenAI
import os
import sqlparse

# OpenAI client (reads OPENAI_API_KEY from environment)
client = OpenAI()

# ---------- Parsers ----------
def load_metrics(metrics_path):
    with open(metrics_path, "r") as f:
        return json.load(f)

def load_flags(flags_path):
    flags = {}
    with open(flags_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                flags[k.strip()] = v.strip()
    return flags

def load_slow_queries(slow_log_path):
    queries = []
    with open(slow_log_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # naive parse: timestamp | duration | query
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                ts, dur, q = parts[0], parts[1], "|".join(parts[2:])
                # duration could be "2500" or "2500 ms"
                m = re.search(r"(\d+)", dur)
                duration_ms = int(m.group(1)) if m else None
                queries.append({"timestamp": ts, "duration_ms": duration_ms, "query": q})
    return queries

# ---------- Heuristic rules for fast recommendations ----------
def heuristic_recommendations(metrics, flags, slow_queries):
    recs = []

    # Instance-level
    cpu = metrics.get("cpu_utilization_pct", 0)
    mem = metrics.get("memory_utilization_pct", 0)
    active_conn = metrics.get("active_connections", 0)
    max_conn = metrics.get("max_connections_configured", 0)
    storage_used = metrics.get("storage_used_gb", 0)
    storage_alloc = metrics.get("storage_allocated_gb", 0)

    if cpu >= 80:
        recs.append({
            "area": "Instance",
            "issue": f"High CPU utilization ({cpu}%)",
            "recommendation": "Consider scaling up instance type (more vCPU) or investigate top CPU-consuming queries.",
            "priority": "High"
        })
    if mem >= 80:
        recs.append({
            "area": "Instance",
            "issue": f"High memory utilization ({mem}%)",
            "recommendation": "Increase memory (bigger machine) or tune buffer_pool/work_mem settings.",
            "priority": "High"
        })
    if storage_used / max(1.0, storage_alloc) >= 0.9:
        recs.append({
            "area": "Storage",
            "issue": f"Storage >90% used ({storage_used}GB/{storage_alloc}GB)",
            "recommendation": "Increase storage or clean old data; enable autoscaling if supported.",
            "priority": "High"
        })
    if active_conn and max_conn and active_conn > (0.8 * max_conn):
        recs.append({
            "area": "Connections",
            "issue": f"Active connections high ({active_conn}/{max_conn})",
            "recommendation": "Introduce connection pooling (PgBouncer/Cloud SQL Proxy) and check for connection leaks.",
            "priority": "Medium"
        })

    # DB flags quick wins
    # innodb_buffer_pool_size: ensure it's ~60-80% of RAM for dedicated DB
    ibps = flags.get("innodb_buffer_pool_size")
    if ibps:
        # try to parse like "16G" or "16384M"
        m = re.match(r"(\d+)([GMK]?)", ibps, re.IGNORECASE)
        if m:
            value = int(m.group(1))
            unit = m.group(2).upper()
            gb = value * (1024**2) / (1024**3) if unit == "M" else value if unit == "G" else value/1024/1024
            # This is heuristic: if buffer pool < 8G warn
            if gb < 8:
                recs.append({
                    "area": "DB Flags",
                    "issue": f"innodb_buffer_pool_size is small ({ibps})",
                    "recommendation": "Increase innodb_buffer_pool_size to reduce disk IO for InnoDB heavy workloads.",
                    "priority": "Medium"
                })

    # Slow query analysis
    for q in slow_queries:
        qtext = q.get("query", "")
        dur = q.get("duration_ms") or 0
        # quick pattern detection
        if dur >= 2000:
            # missing index heuristic: SELECT ... WHERE <col> = ... and no obvious index
            where_match = re.search(r"\bWHERE\s+(.+?)(ORDER BY|GROUP BY|LIMIT|$)", qtext, re.IGNORECASE)
            rec = {
                "area": "Query",
                "issue": f"Slow query ({dur} ms): {qtext[:120]}",
                "recommendation": "Consider adding appropriate indexes, avoid SELECT *, and break large joins. Inspect query plan (EXPLAIN).",
                "priority": "High"
            }
            recs.append(rec)
        elif dur >= 1000:
            recs.append({
                "area": "Query",
                "issue": f"Moderately slow query ({dur} ms): {qtext[:120]}",
                "recommendation": "Review query plan, check indexes, and consider limiting returned columns.",
                "priority": "Medium"
            })

    # Aggregate suggestions (deduplicate similar textual issues)
    seen = set()
    dedup = []
    for r in recs:
        key = (r["area"], r["issue"][:120])
        if key not in seen:
            dedup.append(r)
            seen.add(key)
    return dedup

# ---------- GPT helper for advanced reasoning ----------
def gpt_enhance_recommendations(notes_text, heuristics):
    """
    Sends metrics + heuristics to GPT to get refined recommendations and explanations.
    Returns list of dicts with: area, issue, recommendation, priority, rationale
    """
    # Build prompt
    heur_json = json.dumps(heuristics, indent=2)
    prompt = f"""
You are a Cloud DBA/DevOps expert. Given the following heuristics-based recommendations and raw meeting/metrics notes,
produce an improved, prioritized list of recommendations. For each recommendation return JSON object with:
- area (Instance/Query/Storage/Connections/DB Flags/Other)
- issue (short description)
- recommendation (concrete steps)
- priority (High/Medium/Low)
- rationale (brief)

Heuristics:
{heur_json}

Context/Notes:
{notes_text}

Return only JSON (a list of objects). Ensure JSON is parseable.
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=800
        )
        text = resp.choices[0].message.content
        # Try parse
        return json.loads(text)
    except Exception as e:
        print("GPT enhancement failed:", e)
        # return heuristics as fallback (add rationale)
        for h in heuristics:
            h["rationale"] = "Heuristic generated fallback (GPT unavailable)."
        return heuristics

# ---------- Main ----------
def main(metrics_path, flags_path, slow_log_path, out_csv="outputs/recommendations.csv"):
    os.makedirs("outputs", exist_ok=True)

    metrics = load_metrics(metrics_path)
    flags = load_flags(flags_path)
    slow_queries = load_slow_queries(slow_log_path)

    heuristics = heuristic_recommendations(metrics, flags, slow_queries)

    # Build notes text (concise) to send to GPT for better recommendations
    notes_text = f"Metrics: {json.dumps(metrics)}\nDB Flags: {json.dumps(flags)}\nTop slow queries: {json.dumps(slow_queries[:10])}"

    enhanced = gpt_enhance_recommendations(notes_text, heuristics)

    # Normalize to table rows
    rows = []
    for e in enhanced:
        rows.append({
            "Area": e.get("area", ""),
            "Issue": e.get("issue", ""),
            "Recommendation": e.get("recommendation", ""),
            "Priority": e.get("priority", ""),
            "Rationale": e.get("rationale", "")
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"Saved recommendations to {out_csv}")
    print(df.to_markdown(index=False))

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python agent.py <metrics.json> <db_flags.txt> <slow_queries.log>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])

