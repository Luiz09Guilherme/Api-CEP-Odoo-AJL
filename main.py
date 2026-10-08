from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import re

app = FastAPI(
    title="API Consulta CEP",
    version="1.0.0"
)


class CepRequest(BaseModel):
    cep: str


def normalizar_cep(cep: str) -> str:
    cep = re.sub(r"\D", "", cep)

    if len(cep) != 8:
        raise HTTPException(
            status_code=400,
            detail="CEP inválido. Informe 8 dígitos."
        )

    return cep


def consultar_brasilapi(cep: str):
    url = f"https://brasilapi.com.br/api/cep/v2/{cep}"

    try:
        resposta = requests.get(
            url,
            timeout=10
        )

        if resposta.status_code == 404:
            return None

        resposta.raise_for_status()

        return resposta.json()

    except requests.RequestException:
        return None


def consultar_viacep(cep: str):
    url = f"https://viacep.com.br/ws/{cep}/json/"

    try:
        resposta = requests.get(
            url,
            timeout=10
        )

        resposta.raise_for_status()

        dados = resposta.json()

        if dados.get("erro"):
            return None

        return {
            "cep": dados.get("cep"),
            "logradouro": dados.get("logradouro"),
            "complemento": dados.get("complemento"),
            "bairro": dados.get("bairro"),
            "cidade": dados.get("localidade"),
            "uf": dados.get("uf"),
            "ibge": dados.get("ibge"),
            "ddd": dados.get("ddd"),
            "siafi": dados.get("siafi"),
        }

    except requests.RequestException:
        return None


def padronizar_brasilapi(dados: dict, cep: str):

    cidade = dados.get("city")

    if isinstance(cidade, dict):
        cidade_nome = cidade.get("name")
        ibge = cidade.get("ibge")
    else:
        cidade_nome = cidade
        ibge = None

    estado = dados.get("state")

    if isinstance(estado, dict):
        uf = estado.get("short")
        estado_nome = estado.get("name")
    else:
        uf = estado
        estado_nome = None

    location = dados.get("location") or {}
    coordinates = location.get("coordinates") or {}

    return {
        "cep": dados.get("cep") or cep,
        "logradouro": dados.get("street"),
        "complemento": dados.get("complement"),
        "bairro": dados.get("neighborhood"),
        "cidade": cidade_nome,
        "uf": uf,
        "estado": estado_nome,
        "pais": "Brasil",
        "ibge": ibge,
        "ddd": None,
        "siafi": None,
        "latitude": coordinates.get("latitude"),
        "longitude": coordinates.get("longitude"),
        "timezone": location.get("timezone"),
        "fonte": "BrasilAPI"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/cep")
def consultar_cep(request: CepRequest):

    cep = normalizar_cep(request.cep)

    # BrasilAPI
    dados = consultar_brasilapi(cep)

    if dados:

        resultado = padronizar_brasilapi(
            dados,
            cep
        )

        return {
            "sucesso": True,
            "resultado": resultado
        }

    # ViaCEP como fallback
    dados = consultar_viacep(cep)

    if dados:

        dados["pais"] = "Brasil"
        dados["latitude"] = None
        dados["longitude"] = None
        dados["timezone"] = None
        dados["estado"] = None
        dados["fonte"] = "ViaCEP"

        return {
            "sucesso": True,
            "resultado": dados
        }

    raise HTTPException(
        status_code=404,
        detail={
            "sucesso": False,
            "mensagem": "CEP não encontrado.",
            "cep": cep
        }
    )
