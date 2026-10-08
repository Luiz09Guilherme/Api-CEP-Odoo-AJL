requests.get(
    f"https://viacep.com.br/ws/{cep}/json/",
    timeout=10
)
``` :chatgpt-content-reference{index="0"}


O problema é que essa chamada pode lançar uma exceção — por exemplo, timeout, erro de conexão ou problema de acesso externo — e o nosso código atual **não trata essa exceção**. Por isso o usuário recebe apenas `Internal Server Error`.

Vamos corrigir isso **agora**, e de quebra deixar a API muito mais robusta.

### Substitua seu `main.py` inteiro por este

```python
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

    # =========================================================
    # 1. LIMPA O CEP
    # =========================================================

    cep = ''.join(
        c for c in dados.cep
        if c.isdigit()
    )

    if len(cep) != 8:

        return {
            "sucesso": False,
            "erro": "CEP inválido",
            "cep_recebido": dados.cep
        }


    # =========================================================
    # 2. CONSULTA VIACEP
    # =========================================================

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
            "erro": "A consulta ao serviço de CEP excedeu o tempo limite.",
            "fonte": "ViaCEP"
        }

    except requests.exceptions.RequestException as erro:

        return {
            "sucesso": False,
            "erro": "Não foi possível conectar ao serviço de CEP.",
            "detalhes": str(erro),
            "fonte": "ViaCEP"
        }

    except Exception as erro:

        return {
            "sucesso": False,
            "erro": "Erro inesperado durante a consulta.",
            "detalhes": str(erro)
        }


    # =========================================================
    # 3. VERIFICA RESPOSTA HTTP
    # =========================================================

    if resposta.status_code != 200:

        return {
            "sucesso": False,
            "erro": "O serviço de CEP retornou um erro.",
            "status_http": resposta.status_code,
            "fonte": "ViaCEP"
        }


    # =========================================================
    # 4. CONVERTE JSON
    # =========================================================

    try:

        dados_cep = resposta.json()

    except Exception as erro:

        return {
            "sucesso": False,
            "erro": "O serviço de CEP retornou uma resposta inválida.",
            "detalhes": str(erro)
        }


    # =========================================================
    # 5. CEP NÃO ENCONTRADO
    # =========================================================

    if dados_cep.get("erro"):

        return {
            "sucesso": False,
            "erro": "CEP não encontrado.",
            "cep": cep
        }


    # =========================================================
    # 6. RETORNA DADOS
    # =========================================================

    return {

        "sucesso": True,

        "cep": dados_cep.get(
            "cep"
        ),

        "rua": dados_cep.get(
            "logradouro"
        ),

        "bairro": dados_cep.get(
            "bairro"
        ),

        "cidade": dados_cep.get(
            "localidade"
        ),

        "estado": dados_cep.get(
            "uf"
        ),

        "pais": "Brasil"

    }
