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
        "servico": "API CEP Odoo AJL",
        "versao": "1.1"
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
            "erro": "CEP invalido",
            "cep_recebido": dados.cep
        }

    url = f"https://viacep.com.br/ws/{cep}/json/"

    try:
        resposta = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "API-CEP-Odoo-AJL/1.0"
            }
        )

    except requests.exceptions.Timeout:
        return {
            "sucesso": False,
            "erro": "A consulta ao servico de CEP excedeu o tempo limite.",
            "fonte": "ViaCEP"
        }

    except requests.exceptions.RequestException as erro:
        return {
            "sucesso": False,
            "erro": "Nao foi possivel conectar ao servico de CEP.",
            "detalhes": str(erro),
            "fonte": "ViaCEP"
        }

    except Exception as erro:
        return {
            "sucesso": False,
            "erro": "Erro inesperado durante a consulta.",
            "detalhes": str(erro)
        }

    if resposta.status_code != 200:
        return {
            "sucesso": False,
            "erro": "O servico de CEP retornou um erro.",
            "status_http": resposta.status_code,
            "fonte": "ViaCEP"
        }

    try:
        dados_cep = resposta.json()

    except Exception as erro:
        return {
            "sucesso": False,
            "erro": "O servico de CEP retornou uma resposta invalida.",
            "detalhes": str(erro)
        }

    if dados_cep.get("erro"):
        return {
            "sucesso": False,
            "erro": "CEP nao encontrado.",
            "cep": cep
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
