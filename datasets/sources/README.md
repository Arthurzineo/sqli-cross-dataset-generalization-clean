# Fontes e preparação

Scripts de preparação e referências das bases públicas.

- `ecml/`: preparação do ECML/PKDD 2007.
- `csic/`: decodificação e filtro histórico `INJECTED_PARAM`.
- `srbh/`: seleção inicial do SR-BH 2020.
- `corpus_documentation/`: documentação disponível de todas as bases.

As cópias processadas usadas no estudo estão em `datasets/processed/`. Os
arquivos-fonte originais não são incluídos. Referências de origem:

- ECML/PKDD 2007: [repositório do conjunto](https://gitlab.fing.edu.uy/gsi/web-application-attacks-datasets/-/tree/master/ecml_pkdd) e [página oficial do desafio](https://www.lirmm.fr/pkdd2007-challenge/);
- HTTP CSIC 2010: [repositório do conjunto](https://gitlab.fing.edu.uy/gsi/web-application-attacks-datasets/-/tree/master/csic_2010), [página do CSIC](https://www.tic.itefi.csic.es/dataset/) e [espelho público](https://github.com/msudol/Web-Application-Attack-Datasets).

Quem quiser reconstruir as cópias desde os dados de origem deve obter os
arquivos nesses projetos e conferir os respectivos termos de uso.
O SR-BH é disponibilizado sob CC0 1.0.
Hashes e contagens ficam em `datasets/metadata/` e `provenance/`.
Execute os scripts somente após configurar caminhos locais.
Não substitua arquivos de origem por versões inferidas.
