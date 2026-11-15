# Módulos do estudo

Esta pasta contém a implementação ativa reutilizada pelos experimentos.

- `data/loader.py`: leitura, limpeza de URL e canonicalização iterativa.
- `data/splits.py`: partições por hash, LODO e controles de vazamento.
- `features/lexical.py`: extração dos 64 atributos projetados.
- `features/embeddings.py`: representação densa exploratória.
- `models/classical.py`: Logística, CatBoost e MLP.
- `evaluation/`: execução, registro e métricas de classificação.
- `visualization/`: suporte às visualizações quando aplicável.
- `utils/`: configuração, hashes e persistência de procedência.

Os módulos sustentam a Metodologia e são chamados pelos estágios em `scripts/`.
Execute-os pela raiz do repositório, após instalar `environment/requirements.txt`.
