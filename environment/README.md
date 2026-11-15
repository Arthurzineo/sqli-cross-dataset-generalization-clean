# Ambiente computacional

Arquivos que registram dependências, sistema e máquina do estudo.

- `requirements.txt`: dependências diretas fixadas.
- `pip-freeze.txt`: inventário completo do ambiente original.
- `environment.yml`: alternativa para ambientes Conda.
- `pyproject.toml`: metadados e configuração Python.
- `environment.json`: versões estruturadas registradas.
- `hardware.md`: CPU, memória, GPU e sistema operacional.

Crie um ambiente virtual novo antes de executar o pipeline.
Use Python 3.12 conforme o ambiente registrado.
Diferenças de bibliotecas podem afetar aleatoriedade e serialização.
Nenhuma credencial deve ser colocada nesta pasta.
