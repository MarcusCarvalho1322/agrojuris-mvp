CREATE TABLE IF NOT EXISTS leads (
    nome_infrator TEXT PRIMARY KEY,
    valor_multa NUMERIC,
    tese_primaria TEXT,
    tese_secundaria TEXT,
    status_ia TEXT,
    chance_nulidade TEXT,
    alerta_code TEXT,
    municipio TEXT,
    uf TEXT,
    link_rapido_contato TEXT,
    dat_hora_auto_infracao TEXT,
    score_prioridade NUMERIC,
    volume_credito_cidade NUMERIC,
    num_latitude_auto NUMERIC,
    num_longitude_auto NUMERIC,
    dias_decorridos INTEGER,
    des_infracao TEXT,
    des_status_formulario TEXT,
    link_google_maps TEXT,
    link_socio_proprietario TEXT,
    cpf_cnpj_infrator TEXT,
    des_local_infracao TEXT,
    mapbiomas_lat NUMERIC,
    mapbiomas_lon NUMERIC,
    alertas_encontrados INTEGER,
    motivo_ia TEXT,
    area_ha NUMERIC,
    autorizacao_area NUMERIC
);

CREATE INDEX IF NOT EXISTS leads_status_idx ON leads (status_ia);
CREATE INDEX IF NOT EXISTS leads_uf_idx ON leads (uf);
CREATE INDEX IF NOT EXISTS leads_municipio_idx ON leads (municipio);
CREATE INDEX IF NOT EXISTS leads_score_idx ON leads (score_prioridade);
CREATE INDEX IF NOT EXISTS leads_valor_idx ON leads (valor_multa);
