# Projeto Avaliativo — Suporte de TI (SCTEC Aperfeiçoar)

**Caso:** Relatório Diário de Vendas com dados de sábado ausentes
**Autor:** Lucas Bruno da Costa Mafra
**Data-base do atendimento:** segunda-feira, 23/11/2026

> **Legenda de honestidade técnica (R7).** Todo o caso é **fictício**. Cada ação é marcada:
> **[EXECUTADO]** = realizado de fato pelo autor (ex.: rodar o script local sobre dados sintéticos);
> **[SIMULADO]** = evento do atendimento registrado como se tivesse ocorrido, dentro do cenário fictício;
> **[PROPOSTO]** = ainda não realizado, nem simulado.
> Os logs são **sintéticos**: foram gerados por um script que já embute o cenário. Eles ilustram o raciocínio, não provam nada sobre um ambiente real.

## Navegação

1. [Documentação do projeto](#1-documentação-do-projeto)
2. [Atendimento (obrigatória)](#2-atendimento)
3. [Evidências](#3-evidências)
4. [Comunicação](#4-comunicação)
5. [Solução e conhecimento](#5-solução-e-conhecimento)
6. [Relatório e apresentação](#6-relatório-e-apresentação)

---

## 1. Documentação do projeto

### 1.1 Pacote de contexto do caso (criado pelo autor, fictício)

| Tema | Definição adotada |
| :--- | :--- |
| **Serviço** | Relatório Diário de Vendas (RDV) do Sistema Comercial. Gerado por job agendado e consultado pela equipe comercial por volta das 08h. |
| **Público** | Equipe comercial e gerência comercial. |
| **Ambiente** | Job `rdv_consolidacao` roda às 02h30, todos os dias, e consolida as vendas de D-1. Espera por bloqueio no máximo 30 min (1800 s). **Sem retentativa automática.** Falha é notificada só por e-mail a uma caixa compartilhada de TI, não monitorada pelo N1. |
| **Rotina concorrente** | Backup do banco às 01h00: incremental de segunda a sábado; **completo aos domingos**, com bloqueio de escrita em `vendas_consolidadas`. |
| **Mudança relevante** | CHG-0457, 05/11/2026: ativada a *verificação de integridade* do backup. O completo dominical passou de 01h00–02h20 para 01h00–03h15. |
| **Canais e filas** | Portal de chamados → fila N1 → fila N2 → fila N3 (engenharia). |
| **Prioridade e prazo** | P3 (média): resposta em 4 h; contorno em 1 dia útil; correção definitiva na próxima janela de mudança. |
| **Janela de mudança** | Quartas-feiras, 22h–23h30, com aprovação do coordenador de infraestrutura e plano de reversão. |
| **Alçada N1** | Consultar tela do relatório, data da última atualização, histórico de chamados e KB. Pode pedir ao usuário que limpe o cache ou use outro navegador. **Não** acessa scheduler, logs ou servidores e **não** reexecuta jobs. |
| **Alçada N2** | Ler logs do scheduler e do backup; reexecutar job manualmente **fora da janela de backup** (POP-RDV-01); abrir e executar mudança aprovada de agendamento. |
| **Alçada N3** | Alterar código, consultas e arquitetura (ex.: encadear jobs, reduzir o tempo de bloqueio do backup). |
| **Segurança** | Sem credenciais, tokens ou dados pessoais. Nomes, IDs e e-mails são fictícios. |

### 1.2 Registro de leitura (item 5.1 do enunciado)

| Item | O que o pacote informa | Efeito prático | Dúvida pendente |
| :--- | :--- | :--- | :--- |
| **Serviço crítico** | RDV é relatório gerencial, sem parada operacional | Define impacto médio, não alto | O RDV alimenta algum sistema externo (ex.: financeiro)? |
| **Limite de acesso do N1** | N1 vê só a tela e o status | N1 não pode investigar a causa; precisa coletar evidência indireta e escalar | O N1 pode ler o painel de status do scheduler (sem logs)? |
| **Prazo e janela** | Mudanças só na quarta, 22h–23h30 | A correção definitiva deve estar pronta antes do próximo domingo (29/11) | A janela de 25/11 está livre de outras mudanças? |
| **Procedimento de contorno** | POP-RDV-01 autoriza o N2 a reexecutar o job fora do backup | Restaura os dados sem tocar na configuração | Quem aprova formalmente reexecuções de dias antigos? |
| **Notificação de falha** | E-mail para caixa compartilhada de TI | Explica por que ninguém percebeu as falhas | Quem é o responsável por monitorar essa caixa? |
| **Bloqueio do backup** | Backup completo bloqueia escrita em `vendas_consolidadas` | Sustenta a hipótese de concorrência | O bloqueio dura o backup inteiro ou só parte dele? |

**Pressupostos explícitos:** (a) o job consolida apenas D-1 e, se falha, o dia não é recuperado sozinho; (b) o bloqueio do backup dura toda a execução; (c) o coordenador de infraestrutura é o aprovador formal.
**Lacunas registradas como pendentes:** todas as dúvidas da última coluna. Nenhuma foi tratada como fato.

---

## 2. Atendimento

```text
CASO ESCOLHIDO / JUSTIFICATIVA / CONTEXTO DO SERVIÇO:
Relatório Diário de Vendas com dados de sábado ausentes. Escolhido por ter sintoma
intermitente (só aparece na segunda), várias hipóteses plausíveis a descartar e uma causa
indireta (interação entre duas rotinas). Contexto na seção 1.

TICKET E SOLICITANTE FICTÍCIO:
INC-2026-1123-001 | Marina Costa (gerente comercial, fictícia) | aberto em 23/11/2026, 08h40,
pelo portal de chamados.

SINTOMA E COMPORTAMENTO ESPERADO:
Sintoma: no relatório de hoje (segunda), as vendas de sábado 21/11 estão ausentes; os demais
dias, inclusive domingo, aparecem. A usuária diz ter achado "números baixos" em segundas
anteriores, sem abrir chamado.
Esperado: relatório com todos os dias consolidados (D-1 completo) disponível até as 08h.

CLASSIFICAÇÃO / IMPACTO / URGÊNCIA / PRIORIDADE:
Tipo: incidente (dado incompleto em serviço em operação).
Impacto: MÉDIO. Atinge a equipe comercial e a gerência; decisões baseadas em dado
defasado; sem parada de operação e sem perda de pedidos (as vendas existem no sistema
transacional, só não foram consolidadas).
Urgência: MÉDIA. O problema se repete todo domingo (próxima ocorrência: 29/11, 03h00) e há
fechamento semanal das vendas; não há prazo crítico nas próximas horas.
Prioridade: P3 (média). Se houvesse perda de dados no sistema transacional ou fechamento
financeiro pendente, subiria para P2.

LIMITES DE AUTORIZAÇÃO (ALÇADA):
N1: tela, última atualização, histórico, KB. N2: logs, reexecução via POP-RDV-01, mudança
aprovada. N3: código e arquitetura. Detalhes na seção 1.1.

LINHA DO TEMPO: ver tabela 2.1.

INVESTIGAÇÃO N1 / EVIDÊNCIAS E HIPÓTESES: ver tabelas 2.2 e seção 3.

DECISÃO DE RESOLUÇÃO OU ESCALONAMENTO:
N1 escalona ao N2 (não tem acesso aos logs; sem isso não há como confirmar a causa).
N2 resolve o impacto e propõe a correção. Escalonamento ao N3: NÃO necessário. Justificativa
e condições que o exigiriam: seção 2.3.

HANDOFF N1 -> N2 / CONTORNO N2 / HANDOFF N2 -> N3:
Handoff N1->N2: seção 4 (mensagem 3). Contorno N2: reexecução do job para 07/11, 14/11 e
21/11 [SIMULADO]. Handoff N2->N3: não se aplica, resolvido até o N2 (condições na 2.3).

CAUSA RAIZ E GRAU DE CONFIANÇA:
Causa provável: sobreposição entre o backup completo dominical (alongado de 01h20 para 02h15
de duração pela verificação de integridade, CHG-0457) e o job do relatório às 02h30. O job
espera 1800 s pelo bloqueio, expira (LOCK_TIMEOUT) e não tenta de novo.
Confiança: ALTA, mas não conclusiva. Sustentada por correlação em 3 de 3 domingos pós-mudança
e 0 de 2 antes, e pela mensagem de erro. Falta a prova decisiva: reprodução em homologação
[PROPOSTO]. Fatores contribuintes: ausência de retentativa e alerta mal direcionado.

SOLUÇÃO DEFINITIVA OU PROPOSTA: seção 5 (proposta via mudança na janela de 25/11).

VALIDAÇÃO TÉCNICA E DO USUÁRIO:
Contorno validado pela usuária em 23/11, 11h00 [SIMULADO]. Correção: critérios de aceite na
seção 5.3 [PROPOSTO]; a validação real ocorreria no domingo 29/11.

COMUNICAÇÕES: seção 4.

LIÇÕES APRENDIDAS E ARTIGO (KB ou POP): seção 5.4.

PENDÊNCIAS E RISCOS RESIDUAIS:
(1) Reprodução em homologação não feita. (2) A correção de 25/11 ainda não aplicada; se for
adiada, o problema repete em 29/11. (3) O backup pode crescer e consumir a margem criada.
(4) Dúvidas pendentes da seção 1.2. (5) Pode haver outros relatórios dependentes da mesma tabela.
```

### 2.1 Linha do tempo

| Data/hora | Nível | Ação | Resultado | Status |
| :--- | :--- | :--- | :--- | :--- |
| 05/11, 22h | — | CHG-0457 ativa a verificação de integridade do backup | Backup completo passa a durar mais | Contexto |
| 08/11, 15/11, 22/11, 03h00 | — | Job do RDV falha (LOCK_TIMEOUT) | Sábados 07/11, 14/11 e 21/11 sem consolidação; ninguém é avisado | Contexto |
| 23/11, 08h40 | N1 | Chamado aberto pela usuária | Sintoma registrado e classificado como P3 | [SIMULADO] |
| 23/11, 08h55 | N1 | Reproduz a tela; usuária limpa o cache e testa outro navegador | Mesmo resultado; descarta falha de exibição | [SIMULADO] |
| 23/11, 09h05 | N1 | Levanta datas faltantes nas últimas 4 semanas | Só sábados (07/11, 14/11, 21/11); nada antes de 07/11 | [SIMULADO] |
| 23/11, 09h15 | N1→N2 | Handoff ao N2 sem tocar em servidores | Chamado na fila N2 | [SIMULADO] |
| 23/11, 09h40 | N2 | Lê logs do scheduler | Falhas LOCK_TIMEOUT só aos domingos, 03h00 | [SIMULADO] |
| 23/11, 10h05 | N2 | Compara com o log do backup | Backup dominical termina às 03h15, após o início do job | [SIMULADO] |
| 23/11, 10h20 | N2 | Consulta o histórico de mudanças | CHG-0457 coincide com o início das falhas | [SIMULADO] |
| 23/11, 10h35 | N2 | Reexecuta o job para 07/11, 14/11, 21/11 fora da janela de backup (POP-RDV-01) | Dados consolidados | [SIMULADO] |
| 23/11, 11h00 | N2 | Usuária confere o relatório | Sábados presentes; contorno aceito | [SIMULADO] |
| 23/11, 11h20 | N2 | Abre mudança para a janela de quarta | Aguardando aprovação do coordenador | [SIMULADO] |
| 25/11, 22h | N2 | Aplica a mudança da seção 5.2 | Aguardando execução | [PROPOSTO] |
| 29/11, 03h00 | — | Primeiro domingo após a mudança | Validação conforme a seção 5.3 | [PROPOSTO] |

### 2.2 Investigação: hipótese → teste → resultado → decisão

| # | Hipótese | Teste (nível) | Resultado | Decisão | Evidência |
| :--- | :--- | :--- | :--- | :--- | :--- |
| H1 | O job não está agendado ou foi desabilitado | Consultar o scheduler e o log de execuções (N2) | Job habilitado e executado todos os dias | **Descartada** | E2 |
| H2 | Problema de permissão da conta de serviço | Comparar status da conta nas execuções de segunda a sábado e domingo (N2) | Mesma conta; 6 dias OK e domingo falha | **Descartada** | E2 |
| H3 | Cache ou tela desatualizada | Limpar o cache e usar outro navegador (N1); conferir se os registros existem na tabela consolidada (N2) | Mesmo resultado na tela; registros de sábado inexistentes na tabela | **Descartada** | E1, E2 |
| H4 | Erro de fuso horário ou data de corte | Conferir fuso dos logs e datas consolidadas (N2) | Todos em America/Sao_Paulo; sem deslocamento, a falta é de um dia inteiro | **Descartada** | E2 |
| H5 | Conflito de concorrência com o backup completo | Cruzar janelas do backup e do job (N2, script) | Sobreposição de 45 min e falha em 3 de 3 domingos pós-mudança; 0 de 2 antes | **Sustentada (confiança alta)** | E2, E3, E4, E5 |

### 2.3 Decisão: por que não escalonar ao N3

- **Resolve-se no N2:** o contorno (reexecução) e a correção (reagendamento, retentativa e alerta) cabem na alçada do N2 via POP e mudança aprovada. Não há alteração de código.
- **Escalonamento ao N2 foi necessário:** o N1 não lê logs nem reexecuta jobs.
- **Condições que exigiriam N3:** (a) o job continuar falhando mesmo fora da janela do backup, apontando para a consulta em si; (b) o backup ficar tão longo que não haja horário seguro e seja preciso encadear os jobs ou reduzir o tempo de bloqueio; (c) a causa não se confirmar na reprodução em homologação.

---

## 3. Evidências

Arquivos em `evidencias/`. Todos **sintéticos**, sem dados reais.

| ID | Evidência | Origem | Hipóteses vinculadas | Status |
| :--- | :--- | :--- | :--- | :--- |
| **E1** | Relatório com as datas faltantes (tabela 3.1) | Captura reconstruída, sanitizada | H3, H5 | [SIMULADO] |
| **E2** | `log_relatorio.csv`: 30 execuções do job (25/10 a 23/11) | Gerado por `gerar_dados_sinteticos.py` | H1, H2, H3, H4, H5 | [EXECUTADO] (geração) |
| **E3** | `log_backup.csv`: janelas do backup no mesmo período | Idem | H5 | [EXECUTADO] (geração) |
| **E4** | Registro de mudança CHG-0457 (tabela 3.2) | Texto fictício | H5 | [SIMULADO] |
| **E5** | `resultado_analise.txt`, saída de `analise_concorrencia.py` | Script local, somente leitura | H5 | [EXECUTADO] |

### 3.1 E1: relatório em 23/11 (sanitizado)

| Data consolidada | Registros | Última atualização |
| :--- | :--- | :--- |
| 20/11 (sex) | 1.241 | 21/11 02h50 |
| **21/11 (sáb)** | **— (ausente)** | — |
| 22/11 (dom) | 1.186 | 23/11 02h50 |

O mesmo vazio ocorre em 07/11 e 14/11.

### 3.2 E4: registro de mudança (fictício)

`CHG-0457 | 05/11/2026 22h | Ativar verificação de integridade no backup | Executor: infraestrutura | Impacto declarado: "aumento de duração do backup completo"; não considerou o job do RDV.`

### 3.3 E5: saída da análise [EXECUTADO]

```text
data       backup    fim_bkp verif sobrep_min job   dado_consolidado
2026-10-25 completo  02:20   nao   0          OK    2026-10-24
2026-11-01 completo  02:20   nao   0          OK    2026-10-31
2026-11-08 completo  03:15   sim   45         FALHA 2026-11-07
2026-11-15 completo  03:15   sim   45         FALHA 2026-11-14
2026-11-22 completo  03:15   sim   45         FALHA 2026-11-21

Execucoes analisadas: 30 | falhas: 3 | falhas por dia da semana: {'dom': 3}
Domingos antes da mudanca: 2 (falhas: 0)
Domingos depois da mudanca: 3 (falhas: 3)
Datas sem consolidacao: ['2026-11-07', '2026-11-14', '2026-11-21']
```

### 3.4 Limites da inferência

- **Escopo:** o script mede sobreposição de horários e status do job. Não mede o conteúdo do bloqueio nem o desempenho da consulta.
- **Circularidade:** os dados foram gerados já com a regra "backup longo → job falha". A análise confirma que o script funciona e organiza o raciocínio, **não** valida a causa em ambiente real.
- **Amostra:** 5 domingos é pouco. Ausência de falha antes da mudança não prova ausência de outras causas.
- **Escala em produção:** seriam necessárias pelo menos 8 a 12 semanas de observação, mais a métrica de bloqueios do banco.
- **Privacidade:** em um log real seriam removidos usuários, hosts, IPs, nomes de tabelas sensíveis e quaisquer credenciais.

---

## 4. Comunicação

**Mensagem 1: abertura (para a usuária, 23/11, 08h45) [SIMULADO]**
> Olá, Marina. Recebi seu chamado INC-2026-1123-001 sobre as vendas de sábado que não aparecem no relatório. Vou verificar se o problema é só de exibição ou se o dado não foi consolidado. Volto a falar com você até as 10h30 com uma posição. Se tiver exemplos de outras segundas com o mesmo problema, pode me enviar.

**Mensagem 2: atualização (para a usuária, 23/11, 09h20) [SIMULADO]**
> Marina, o problema não é de exibição: os dados de sábado realmente não foram consolidados, e o mesmo ocorreu em 07/11 e 14/11. Passei o caso à equipe de infraestrutura, que tem acesso aos registros do sistema. Retorno às 11h00 com a atualização. Nada precisa ser feito por você agora.

**Mensagem 3: handoff N1 → N2 (interna, 23/11, 09h15) [SIMULADO]**
```text
Resumo: RDV sem dados de sábado (21/11, 14/11, 07/11). Impacto: médio, equipe comercial. P3.
Evidências N1: tela reproduz; cache limpo e outro navegador sem efeito; lacunas só em sábados.
Testes: H3 (cache/tela) descartada no nível N1.
Alçada: N1 não acessa logs nem reexecuta jobs; nada foi alterado em servidores.
Suspeita: falha do job de domingo, 03h00 (hipótese, não confirmada). Confiança: baixa.
Próximo passo sugerido: ler logs do scheduler e do backup de domingo.
Retorno à usuária: 11h00.
```

**Mensagem 4: encerramento do contorno (para a usuária, 23/11, 11h05) [SIMULADO]**
> Marina, reprocessamos os sábados que faltavam (07/11, 14/11 e 21/11) e você já pode conferir o relatório. A causa provável é que o backup de domingo passou a demorar mais e acabou impedindo a geração do relatório. Para evitar que se repita, uma correção está prevista para quarta-feira, 25/11, à noite. Vou confirmar o resultado na segunda-feira, 30/11, às 09h, depois do primeiro domingo com o ajuste. Se notar qualquer dia faltando antes disso, responda este chamado.

**Mensagem 5: pedido de mudança (para o aprovador, 23/11, 11h20) [SIMULADO]**
> Solicito aprovação para a mudança da seção 5.2, na janela de 25/11, 22h. Risco: baixo (há plano de reversão). Se não for aprovada, o problema se repete em 29/11 às 03h00.

---

## 5. Solução e conhecimento

### 5.1 Contorno × correção

| | Contorno | Correção definitiva |
| :--- | :--- | :--- |
| **O que é** | Reexecutar o job para as datas faltantes fora da janela do backup | Reagendar o job, adicionar retentativa e corrigir o alerta |
| **Resolve a causa?** | Não. Só repõe os dados | Sim, se a causa estiver correta |
| **Nível e base** | N2, POP-RDV-01 | N2, mudança aprovada |
| **Status** | [SIMULADO] em 23/11 | [PROPOSTO] para 25/11 |

### 5.2 Mudança proposta

**Alternativas e trade-offs**

| Opção | Vantagem | Risco |
| :--- | :--- | :--- |
| **A.** Mover o job para 04h00 (horário fixo) | Simples, dentro da alçada do N2, pronto antes de 29/11 | Margem de 45 min após o backup; se o backup crescer, volta a falhar |
| **B.** Encadear: o job inicia quando o backup completo termina | Robusta, acompanha o tamanho do backup | Exige mudança na orquestração; provável escopo do N3, não cabe até 29/11 |
| **C.** Reduzir o bloqueio do backup | Ataca a raiz | Depende de engenharia e de teste; prazo incerto |

**Escolha:** A agora, com retentativa e alerta, e B registrada como melhoria para o N3. A é a única que cabe na alçada e no prazo; a fragilidade dela é compensada pelo alerta.

**Itens da mudança [PROPOSTO]**
1. Mover `rdv_consolidacao` de 02h30 para 04h00.
2. Retentativa: até 3 tentativas com intervalo de 30 min.
3. Redirecionar o alerta de falha para a fila N2, com cópia ao N1.
4. Alerta preventivo se o backup completo terminar depois das 03h30.

**Plano de reversão:** antes da mudança, exportar a configuração atual do job (02h30, sem retentativa) e restaurá-la se o job falhar no teste manual ou se surgir conflito com outro job. Atenção: a reversão devolve o problema original.

### 5.3 Validação

| Critério de aceite | Quando | Status |
| :--- | :--- | :--- |
| Execução manual de teste fora da janela termina com sucesso | 25/11, após a mudança | [PROPOSTO] |
| Domingo 29/11: backup termina antes do início do job (04h00) | 29/11 | [PROPOSTO] |
| Job de 29/11 com status OK e sábado 28/11 consolidado | 29/11, 04h30 | [PROPOSTO] |
| Usuária confirma o relatório completo | 30/11, 09h | [PROPOSTO] |
| Nenhum alerta de falha ou de atraso do backup | 29/11 | [PROPOSTO] |

### 5.4 Artigo de conhecimento (KB)

**KB-RDV-001: Relatório diário com um dia faltando**

- **Sintoma:** o relatório mostra todos os dias, menos um (padrão: sábado, visto na segunda).
- **Quando usar:** dado ausente de um dia inteiro, não valores errados.
- **Checklist do N1 (sem acesso a logs):**
  1. Registrar qual data falta e quais outras semanas têm a mesma lacuna.
  2. Limpar o cache e testar outro navegador.
  3. Anotar o dia da semana e a hora da última atualização exibida.
  4. Se a lacuna se repete em dia fixo, **escalonar ao N2**; não reiniciar nada.
- **Diagnóstico do N2:** ver o log do job no dia seguinte à data faltante; procurar `LOCK_TIMEOUT`; comparar a janela do backup no mesmo dia; verificar mudanças recentes no backup.
- **Contorno:** reexecutar o job para as datas faltantes **fora** da janela do backup (POP-RDV-01).
- **Correção:** separar os horários do job e do backup; retentativa; alerta para a fila correta.
- **Prevenção:** toda mudança no backup deve listar os jobs que dependem da mesma tabela.
- **Quando escalar ao N3:** falha persistente fora da janela do backup ou ausência de horário seguro disponível.

---

## 6. Relatório e apresentação

- **Relatório técnico (PDF):** `relatorio_tecnico.pdf`, com os 14 tópicos do item 5.6.
- **Síntese analítica:** o incidente decorreu da interação entre duas rotinas corretas isoladamente: um backup que ficou mais longo após uma mudança e um job sem tolerância a espera. A falha ficou invisível por três semanas porque o alerta ia para uma caixa que ninguém monitora.
- **Limitações:** dados sintéticos; confiança alta, não conclusiva; sem reprodução em homologação; correção e validação só propostas.
- **Aprendizado:** (1) toda mudança deve mapear dependências; (2) alerta sem dono equivale a não ter alerta; (3) o contorno devolve o dado, mas só a correção evita a repetição.
