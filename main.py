from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()


class CEPRequest(BaseModel):
    cep: str


@app.get("/")
def home():
    return {
        "status": "online",
        "servico": "API CEP Odoo AJL"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/cep")
def consultar_cep(dados: CEPRequest):

    cep = ''.join(
        c for c in dados.cep
        if c.isdigit()
    )

    if len(cep) != 8:
        return {
            "sucesso": False,
            "erro": "CEP inválido"
        }

    url = f"https://viacep.com.br/ws/{cep}/json/"

    resposta = requests.get(
        url,
        timeout=10
    )

    if resposta.status_code != 200:
        return {
            "sucesso": False,
            "erro": "Erro ao consultar CEP"
        }

    dados_cep = resposta.json()

    if dados_cep.get("erro"):
        return {
            "sucesso": False,
            "erro": "CEP não encontrado"
        }

    return {
        "sucesso": True,
        "cep": dados_cep.get("cep"),
        "rua": dados_cep.get("logradouro"),
        "bairro": dados_cep.get("bairro"),
        "cidade": dados_cep.get("localidade"),
        "estado": dados_cep.get("uf"),
        "pais": "Brasil"
    }
