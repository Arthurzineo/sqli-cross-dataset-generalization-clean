# Ferramentas de manutenção

Utilitários para verificar e preparar o pacote publicável.

- `build_inventory.py`: inventário de arquivos e tamanhos.
- `security_scan.py`: busca local por segredos e dados sensíveis.
- `verify_saved_outputs.py`: confere resultados compactos persistidos.

Essas ferramentas não treinam detectores.
Execute-as pela raiz do repositório.
Revise manualmente falsos positivos de segurança.
Não use o inventário como substituto dos manifests científicos.
Antes de publicar, combine a varredura local com `gitleaks`.
Registre no relatório qualquer exceção preservada por hash.
