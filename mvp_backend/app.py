import os
import json
from typing import Optional
from dotenv import load_dotenv
from fastapi import HTTPException
from pathlib import Path

load_dotenv(override=False)

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from db import get_conn

app = FastAPI(title="AgroDefesa MVP API", version="0.1.0")
FALLBACK_PATH = Path(__file__).parent / "fallback_leads.json"
_fallback_cache = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


def get_fallback_rows():
    global _fallback_cache
    if _fallback_cache is not None:
        return _fallback_cache
    if not FALLBACK_PATH.exists():
        return []
    with open(FALLBACK_PATH, "r", encoding="utf-8") as f:
        _fallback_cache = json.load(f)
    return _fallback_cache


def fallback_stats(rows):
    by_status = {}
    for row in rows:
        key = row.get("status_ia") or ""
        by_status[key] = by_status.get(key, 0) + 1
    return {"total": len(rows), "by_status": by_status}


def fallback_filters(rows):
    ufs = sorted({r.get("uf") for r in rows if r.get("uf")})
    municipios = sorted({r.get("municipio") for r in rows if r.get("municipio")})
    statuses = sorted({r.get("status_ia") for r in rows if r.get("status_ia")})
    return {"ufs": ufs, "municipios": municipios, "statuses": statuses}


def fallback_leads(
    rows,
    status_ia: Optional[str],
    uf: Optional[str],
    municipio: Optional[str],
    min_multa: Optional[float],
    max_multa: Optional[float],
    search: Optional[str],
    limit: int,
    offset: int,
    sort: str,
):
    filtered = rows
    if status_ia:
        filtered = [r for r in filtered if (r.get("status_ia") or "") == status_ia]
    if uf:
        filtered = [r for r in filtered if (r.get("uf") or "") == uf]
    if municipio:
        filtered = [r for r in filtered if (r.get("municipio") or "") == municipio]
    if min_multa is not None:
        filtered = [r for r in filtered if (r.get("valor_multa") or 0) >= min_multa]
    if max_multa is not None:
        filtered = [r for r in filtered if (r.get("valor_multa") or 0) <= max_multa]
    if search:
        s = search.lower()
        filtered = [r for r in filtered if s in (r.get("nome_infrator") or "").lower()]

    if sort == "multa":
        filtered.sort(key=lambda x: x.get("valor_multa") or 0, reverse=True)
    else:
        filtered.sort(key=lambda x: x.get("score_prioridade") or 0, reverse=True)

    items = filtered[offset: offset + limit]
    return {"items": items, "limit": limit, "offset": offset}


@app.get("/stats")
def stats():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM leads")
                total = cur.fetchone()[0]
                cur.execute(
                    "SELECT status_ia, COUNT(*) FROM leads GROUP BY status_ia ORDER BY COUNT(*) DESC"
                )
                by_status = {row[0] or "": row[1] for row in cur.fetchall()}
    except Exception:
        rows = get_fallback_rows()
        if rows:
            return fallback_stats(rows)
        raise HTTPException(status_code=503, detail="DB error on /stats and no fallback data")

    return {"total": total, "by_status": by_status}


@app.get("/filters")
def filters():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT uf FROM leads WHERE uf IS NOT NULL ORDER BY uf")
                ufs = [r[0] for r in cur.fetchall() if r[0]]
                cur.execute("SELECT DISTINCT municipio FROM leads WHERE municipio IS NOT NULL ORDER BY municipio")
                municipios = [r[0] for r in cur.fetchall() if r[0]]
                cur.execute("SELECT DISTINCT status_ia FROM leads WHERE status_ia IS NOT NULL ORDER BY status_ia")
                statuses = [r[0] for r in cur.fetchall() if r[0]]
    except Exception:
        rows = get_fallback_rows()
        if rows:
            return fallback_filters(rows)
        raise HTTPException(status_code=503, detail="DB error on /filters and no fallback data")

    return {"ufs": ufs, "municipios": municipios, "statuses": statuses}


@app.get("/leads")
def leads(
    status_ia: Optional[str] = None,
    uf: Optional[str] = None,
    municipio: Optional[str] = None,
    min_multa: Optional[float] = None,
    max_multa: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort: str = "score",
):
    where = []
    params = []

    if status_ia:
        where.append("status_ia = %s")
        params.append(status_ia)
    if uf:
        where.append("uf = %s")
        params.append(uf)
    if municipio:
        where.append("municipio = %s")
        params.append(municipio)
    if min_multa is not None:
        where.append("valor_multa >= %s")
        params.append(min_multa)
    if max_multa is not None:
        where.append("valor_multa <= %s")
        params.append(max_multa)
    if search:
        where.append("nome_infrator ILIKE %s")
        params.append(f"%{search}%")

    order_by = "score_prioridade DESC"
    if sort == "multa":
        order_by = "valor_multa DESC"

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    sql = (
        "SELECT nome_infrator, valor_multa, tese_primaria, tese_secundaria, status_ia, chance_nulidade, "
        "alerta_code, municipio, uf, link_rapido_contato, dat_hora_auto_infracao, score_prioridade "
        f"FROM leads {where_sql} ORDER BY {order_by} LIMIT %s OFFSET %s"
    )

    params.extend([limit, offset])

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
    except Exception:
        rows = get_fallback_rows()
        if rows:
            return fallback_leads(
                rows,
                status_ia,
                uf,
                municipio,
                min_multa,
                max_multa,
                search,
                limit,
                offset,
                sort,
            )
        raise HTTPException(status_code=503, detail="DB error on /leads and no fallback data")

    keys = [
        "nome_infrator",
        "valor_multa",
        "tese_primaria",
        "tese_secundaria",
        "status_ia",
        "chance_nulidade",
        "alerta_code",
        "municipio",
        "uf",
        "link_rapido_contato",
        "dat_hora_auto_infracao",
        "score_prioridade",
    ]

    data = [dict(zip(keys, row)) for row in rows]
    return {"items": data, "limit": limit, "offset": offset}


@app.get("/top100")
def top100():
    return leads(limit=100, offset=0, sort="score")


@app.get("/top30")
def top30():
    return leads(limit=30, offset=0, sort="score")
