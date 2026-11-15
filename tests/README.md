# Testes

Testes rápidos dos módulos centrais do pipeline.

- `test_loader.py`: carregamento, limpeza e canonicalização.
- `test_splits.py`: isolamento dos grupos e partições.
- `test_lexical.py`: dimensões e comportamento do extrator.

Eles não executam a grade experimental nem substituem a validação científica.
Instale as dependências antes de rodar.

```bash
python -m pytest tests
```

Falhas devem ser corrigidas antes de iniciar novos treinamentos.
