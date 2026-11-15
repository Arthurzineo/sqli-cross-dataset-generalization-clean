# Execução dos experimentos

Na coleção controlada, cada ajuste é executado sequencialmente em um
subprocesso. O supervisor limita cada processo a duas threads e a 12 GiB de
espaço de endereçamento, além de exigir ao menos 2 GiB de RAM disponível antes
do ajuste. Os arquivos de atributos são acessados por mapeamento em memória.
Esses controles estão em `scripts/supplemental/run.py` e em
`scripts/supplemental/config.json`.

O limite de 12 GiB é aplicado com `RLIMIT_AS`; portanto, representa espaço de
endereçamento e não um teto medido de memória física residente. Os checkpoints
de modelos ficam desativados nessa coleção. Métricas, partições, probabilidades,
predições e hashes são persistidos para auditar as execuções e retomar a fila.

Na coleção histórica, o executor e o CatBoost recebem duas threads. A
configuração declara um orçamento de 13 GiB, mas esse valor não constitui, por
si só, um limite físico aplicado. Os controles rígidos do supervisor da coleção
controlada não devem ser atribuídos retroativamente à coleção histórica.

Os três detectores principais são ajustados em CPU. A GPU é usada apenas no
caminho suplementar de representações densas. O inventário completo do ambiente
está em `environment/`.
