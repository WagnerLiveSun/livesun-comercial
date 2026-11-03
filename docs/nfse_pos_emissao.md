# Conclusão integrada da emissão de NFS-e

## Comportamento

- Não há sequência interna nova nem previsão do número da SEFIN.
- O retorno é lido por `src/services/nfse_retorno.py`: XML puro, base64,
  gzip/base64 e identificadores explícitos no JSON. O XML autorizado prevalece.
- DPS não é aceita como XML de NFS-e. Ausência de campos opcionais não descarta
  o número oficial encontrado.
- A operação e a fila são gravadas antes da transmissão. O XML enviado é o
  mesmo reservado na emissão. A restrição existente de empresa/hash protege
  a operação contra gravações concorrentes; não há nova tabela ou migração.
- A emissão fiscal é gravada antes da integração financeira. A integração usa
  o serviço local com bloqueio da emissão e número oficial, nunca o interno.
- O sucesso do formulário redireciona para a conclusão com prévia HTML do
  DANFS-e e formulário de e-mail preenchido. A prévia não chama `window.print`.
- O download gera PDF com o mesmo template usado no anexo do e-mail.
- O e-mail só é enviado por POST confirmado pelo usuário; número, assunto e
  anexo são preparados após recuperar os identificadores fiscais.
- Falhas financeiras, de PDF ou de e-mail não retransmitem a DPS.

## Notas existentes

Abrir os detalhes, a visualização ou a conclusão recupera o número do XML ou
retorno local. A listagem recupera notas sem número na página carregada.
Em **DANFS-e e E-mail**, o botão **Recuperar dados sem reemitir** permite
consultar pela chave caso o XML não esteja armazenado. Isso faz consulta GET,
nunca uma nova emissão. O financeiro pendente pode ser concluído pelo botão
específico, sujeito à permissão financeira, ou pela integração manual existente.

Nenhuma nota de produção é alterada durante a instalação; a recuperação ocorre
ao acessar os processos acima. Não há varredura automática de todo o banco.

## Retorno incerto e limites

Em timeout, a emissão permanece pendente e a fila passa para `VERIFICAR`.
A repetição da mesma operação encontra a reserva e não transmite novamente.
Se não houver chave nem XML após interrupção, a situação precisa ser conferida
antes de qualquer nova tentativa. Não há retentativa automática nem consulta
por identificador de DPS implementada nesta alteração.

O critério de hash fiscal existente foi preservado para manter compatibilidade
com operações antigas. Ele não foi substituído por token por formulário:
emissões intencionalmente idênticas continuam sujeitas à deduplicação existente.

## Validação local

Executar `python -m pytest tests/test_nfse_pos_emissao.py
tests/test_nfse_integracao_financeira.py tests/test_nfse_municipios.py
tests/test_nfse_signature_reference.py -q` a partir da raiz do projeto.
Os testes usam retornos sintéticos e transporte/e-mail simulados, sem chamadas
reais à SEFIN e sem envio de mensagens. Também cobrem a ordem dos commits,
repetição do POST, timeout e falhas posteriores à autorização.

A geração binária real do PDF depende do WeasyPrint e bibliotecas nativas
instalados no servidor, como já exigido pelo processo de e-mail existente.

Na validação de 03/11/2026, o Windows local não tinha `libgobject-2.0-0`;
a renderização HTML real foi testada, mas o PDF binário foi simulado nos testes
de rota. Após as correções de preparação do deploy, a execução de
`python -m pytest tests src/tests -q` passou com 185 testes aprovados,
1 ignorado e 967 subtestes aprovados. A configuração de testes desativa
o Asaas e usa chave de sessão exclusiva de testes, sem herdar esses valores
do ambiente de produção.