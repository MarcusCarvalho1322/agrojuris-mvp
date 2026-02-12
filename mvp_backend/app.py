import os
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from db import get_conn

load_dotenv()

app = FastAPI(title="AgroDefesa MVP API", version="0.1.0")

origins = [
    os.getenv("FRONTEND_ORIGIN", "*")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM leads")
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT status_ia, COUNT(*) FROM leads GROUP BY status_ia ORDER BY COUNT(*) DESC"
            )
            by_status = {row[0] or "": row[1] for row in cur.fetchall()}

    return {"total": total, "by_status": by_status}


@app.get("/filters")
def filters():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT uf FROM leads WHERE uf IS NOT NULL ORDER BY uf")
            ufs = [r[0] for r in cur.fetchall() if r[0]]
            cur.execute("SELECT DISTINCT municipio FROM leads WHERE municipio IS NOT NULL ORDER BY municipio")
            municipios = [r[0] for r in cur.fetchall() if r[0]]
            cur.execute("SELECT DISTINCT status_ia FROM leads WHERE status_ia IS NOT NULL ORDER BY status_ia")
            statuses = [r[0] for r in cur.fetchall() if r[0]]

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

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

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
