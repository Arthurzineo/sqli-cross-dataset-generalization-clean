# Configurações

Arquivos YAML consumidos pelo pipeline ativo.

- `datasets.yaml`: famílias, arquivos, separadores, campos e rótulos.
- `models.yaml`: hiperparâmetros dos três classificadores.
- `seeds.yaml`: sementes 42, 123, 2026, 1337 e 9001.
- `experiments.yaml`: cenários, representações e grades experimentais.
- `paths.yaml`: diretórios relativos usados pelas etapas.

As configurações sustentam a descrição experimental da Metodologia.
Os caminhos devem ser relativos à raiz do repositório.
Não coloque credenciais ou alvos reais nestes arquivos.
As cópias em `experiments/configs/` registram a organização experimental.
