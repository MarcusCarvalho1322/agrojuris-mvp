import csv
from pathlib import Path
from dotenv import load_dotenv
from db import get_conn

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "LISTA_DIAMANTE_MATRIZ_TESES_2026.csv"
MAPBIOMAS_PATH = ROOT / "RELATORIO_MAPBIOMAS_API.csv"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

STATUS_WEIGHT = {
    "NULIDADE ALTA": 1000,
    "VERIFICAR EMBARGO": 700,
    "REVISAR": 300,
    "SEM ALERTAS": 0,
    "": 0,
}


def to_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    value = value.replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def to_int(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def compute_score(status_ia, valor_multa):
    status = (status_ia or "").strip().upper()
    base = STATUS_WEIGHT.get(status, 0)
    valor = valor_multa or 0
    return base + (valor / 100000)


def read_mapbiomas():
    data = {}
    with open(MAPBIOMAS_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            name = row.get("NOME_INFRATOR")
            if not name:
                continue
            data[name] = row
    return data


def load_rows():
    mb_map = read_mapbiomas()
    rows = []

    with open(MATRIX_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            name = row.get("NOME_INFRATOR")
            if not name:
                continue

            mb = mb_map.get(name, {})

            valor_multa = to_float(row.get("VALOR_MULTA"))
            score = compute_score(mb.get("STATUS_IA"), valor_multa)

            rows.append({
                "NOME_INFRATOR": name,
                "VALOR_MULTA": valor_multa,
                "TESE_PRIMARIA": row.get("TESE_PRIMARIA"),
                "TESE_SECUNDARIA": row.get("TESE_SECUNDARIA"),
                "STATUS_IA": mb.get("STATUS_IA"),
                "CHANCE_NULIDADE": mb.get("CHANCE_NULIDADE"),
                "ALERTA_CODE": mb.get("ALERTA_CODE"),
                "MUNICIPIO": row.get("MUNICIPIO"),
                "UF": row.get("UF"),
                "LINK_RAPIDO_CONTATO": row.get("LINK_RAPIDO_CONTATO"),
                "DAT_HORA_AUTO_INFRACAO": row.get("DAT_HORA_AUTO_INFRACAO"),
                "SCORE_PRIORIDADE": score,
                "VOLUME_CREDITO_CIDADE": to_float(row.get("VOLUME_CREDITO_CIDADE")),
                "NUM_LATITUDE_AUTO": to_float(row.get("NUM_LATITUDE_AUTO")),
                "NUM_LONGITUDE_AUTO": to_float(row.get("NUM_LONGITUDE_AUTO")),
                "DIAS_DECORRIDOS": to_int(row.get("DIAS_DECORRIDOS")),
                "DES_INFRACAO": row.get("DES_INFRACAO"),
                "DES_STATUS_FORMULARIO": row.get("DES_STATUS_FORMULARIO"),
                "LINK_GOOGLE_MAPS": row.get("LINK_GOOGLE_MAPS"),
                "LINK_SOCIO_PROPRIETARIO": row.get("LINK_SOCIO_PROPRIETARIO"),
                "CPF_CNPJ_INFRATOR": row.get("CPF_CNPJ_INFRATOR"),
                "DES_LOCAL_INFRACAO": row.get("DES_LOCAL_INFRACAO"),
                "LAT": to_float(mb.get("LAT")),
                "LON": to_float(mb.get("LON")),
                "ALERTAS_ENCONTRADOS": to_int(mb.get("ALERTAS_ENCONTRADOS")),
                "MOTIVO_IA": mb.get("MOTIVO_IA"),
                "AREA_HA": to_float(mb.get("AREA_HA")),
                "AUTORIZACAO_AREA": to_float(mb.get("AUTORIZACAO_AREA")),
            })

    # dedup by NOME_INFRATOR
    seen = set()
    deduped = []
    for row in rows:
        if row["NOME_INFRATOR"] in seen:
            continue
        seen.add(row["NOME_INFRATOR"])
        deduped.append(row)

    return deduped


def apply_schema(conn):
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema_sql)
        conn.commit()


def load_to_db(rows):
    cols = [
        "NOME_INFRATOR",
        "VALOR_MULTA",
        "TESE_PRIMARIA",
        "TESE_SECUNDARIA",
        "STATUS_IA",
        "CHANCE_NULIDADE",
        "ALERTA_CODE",
        "MUNICIPIO",
        "UF",
        "LINK_RAPIDO_CONTATO",
        "DAT_HORA_AUTO_INFRACAO",
        "SCORE_PRIORIDADE",
        "VOLUME_CREDITO_CIDADE",
        "NUM_LATITUDE_AUTO",
        "NUM_LONGITUDE_AUTO",
        "DIAS_DECORRIDOS",
        "DES_INFRACAO",
        "DES_STATUS_FORMULARIO",
        "LINK_GOOGLE_MAPS",
        "LINK_SOCIO_PROPRIETARIO",
        "CPF_CNPJ_INFRATOR",
        "DES_LOCAL_INFRACAO",
        "LAT",
        "LON",
        "ALERTAS_ENCONTRADOS",
        "MOTIVO_IA",
        "AREA_HA",
        "AUTORIZACAO_AREA",
    ]

    with get_conn() as conn:
        apply_schema(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE leads")
            args_str = ",".join(["%s"] * len(cols))
            insert_sql = (
                "INSERT INTO leads ("
                "nome_infrator, valor_multa, tese_primaria, tese_secundaria, status_ia, chance_nulidade, "
                "alerta_code, municipio, uf, link_rapido_contato, dat_hora_auto_infracao, score_prioridade, "
                "volume_credito_cidade, num_latitude_auto, num_longitude_auto, dias_decorridos, des_infracao, "
                "des_status_formulario, link_google_maps, link_socio_proprietario, cpf_cnpj_infrator, "
                "des_local_infracao, mapbiomas_lat, mapbiomas_lon, alertas_encontrados, motivo_ia, area_ha, autorizacao_area"
                ") VALUES (" + args_str + ")"
            )

            values = [tuple(row.get(col) for col in cols) for row in rows]
            cur.executemany(insert_sql, values)
            conn.commit()


if __name__ == "__main__":
    data = load_rows()
    load_to_db(data)
    print(f"OK: loaded {len(data)} rows")
