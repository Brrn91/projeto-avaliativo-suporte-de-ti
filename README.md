# Atendimento - SCTEC

Agente de **Service Desk (N1)** que roda inteiramente no navegador, em um único arquivo `index.html`. Você faz o papel do cliente; o agente conduz a triagem com poucas perguntas, mostra o raciocínio, preenche a ficha do chamado e gera um relatório em PDF.

Projeto desenvolvido no **SCTEC Aperfeiçoar — Suporte de TI**. Todos os dados são **fictícios**.

## O que ele faz

- **Triagem guiada:** identifica o caso a partir do relato (por palavras-chave), faz só as perguntas necessárias e pula as que o cliente já respondeu no relato.
- **Painel de raciocínio:** hipótese atual, barra de confiança (Baixa, Média ou Alta) e, para cada pergunta, o motivo de ela ser feita e a leitura da resposta (apoia, diverge ou não confirma).
- **Ficha do chamado:** cliente, serviço, tipo, prioridade com justificativa, hipótese, contorno, encaminhamento e próxima atualização, preenchida durante a conversa.
- **Relatório em PDF:** um relatório por sessão, com a ficha, o raciocínio, a mensagem ao cliente e a nota de handoff N1 → N2 (usa a janela de impressão do navegador: "Salvar como PDF").
- **Segurança:** o agente nunca pede senha, token, código de verificação ou CPF. Se o usuário digitar algum, o trecho é removido antes de aparecer na conversa, na ficha e no PDF.
- **Base de conhecimento editável:** guardada no navegador (`localStorage`), com backup e restauração em JSON e importação de casos a partir de relatórios (PDF, TXT, MD ou JSON), sempre com pré-visualização antes de salvar.
- **Acessibilidade e uso em celular:** layout responsivo, foco visível, botões A− e A+ para o tamanho do texto.

## Casos incluídos

| ID | Caso |
| :--- | :--- |
| `INC-0533` | Sistema financeiro inacessível (falha de resolução de nome) |
| `INC-2026-1123-001` | Relatório diário de vendas com dados de sábado ausentes (conflito entre o job do relatório e o backup completo de domingo) |

## Como usar

1. Baixe ou clone o repositório.
2. Abra o `index.html` no navegador. Não há build, servidor nem chave de API.
3. Informe seu nome e setor e descreva o problema. Exemplos de relato:
   - "Não consigo entrar no sistema financeiro e hoje é o último dia dos pagamentos"
   - "O relatório de vendas está sem os dados de sábado"

> A leitura de PDF na importação carrega o `pdf.js` por CDN, então precisa de internet. O resto funciona offline.

## Publicar no Render (site estático)

1. Suba o repositório no GitHub.
2. No Render, crie um **Static Site** apontando para o repositório.
3. Deixe o **Build Command** vazio e use `.` como **Publish Directory**.

Também funciona no GitHub Pages (Settings → Pages → branch `main`, pasta raiz).

## Como o agente decide

Não usa IA generativa nem API externa. A lógica é determinística:

1. **Identificação do caso:** soma pontos por palavra-chave encontrada no relato (frases valem mais). O caso só é escolhido se vencer com clareza; senão, o agente pede que você escolha entre as opções.
2. **Perguntas:** cada pergunta tem `sinais_que_confirmam` e `sinais_que_contradizem`. A resposta do cliente é lida contra esses sinais.
3. **Confiança:** *Baixa* se as divergências forem iguais ou maiores que as confirmações; *Alta* se tudo confirmou e nada divergiu; *Média* nos demais casos.
4. **Sem caso na base:** após duas tentativas, o relato é registrado e encaminhado ao N2.

**Limitação:** a correspondência por palavras-chave é simples. Relatos muito diferentes dos exemplos podem cair em "caso não catalogado".

## Formato de um caso na base

Cada caso é um objeto JSON. Os campos obrigatórios são `id`, `titulo`, `palavras_chave`, `perguntas_chave` e `hipotese_n1`.

```json
{
  "id": "INC-0000",
  "versao": 1,
  "titulo": "Título do caso",
  "sintoma": "Frase curta mostrada como sugestão",
  "palavras_chave": ["termo", "outro termo"],
  "perguntas_chave": [{
    "campo": "abrangencia",
    "rotulo": "Abrangência",
    "pergunta": "Mais pessoas têm o mesmo problema?",
    "por_que": "Por que essa pergunta importa.",
    "resposta_tipica": "Sim, a equipe toda.",
    "sinais_que_confirmam": ["todos", "equipe"],
    "sinais_que_contradizem": ["só eu"]
  }],
  "pergunta_impacto": "Isso atrapalha algum prazo?",
  "hipotese_n1": "Hipótese que o N1 consegue sustentar.",
  "tipo": "Incidente",
  "categoria": "Categoria",
  "prioridade": "P3 — Média",
  "justificativa_prioridade": "Impacto e urgência.",
  "contorno": "O que o cliente pode fazer enquanto isso.",
  "encaminhar_para": "N2",
  "proxima_verificacao": "O que o N2 verifica primeiro.",
  "causa_raiz": "...",
  "solucao": "...",
  "artigo_kb": "..."
}
```

Para atualizar um caso existente, importe um relatório com o mesmo `id`: a versão aumenta em 1 e as perguntas-chave originais são preservadas.

## Estrutura

```text
.
├── index.html   # aplicação completa (HTML, CSS, JS e base inicial)
└── README.md
```

## Autor

**Lucas Bruno da Costa Mafra** — SCTEC Aperfeiçoar.
Mentor: Thiago F. de Souza Areco.

## Aviso

Material educacional. Nomes, chamados, registros e evidências são fictícios ou sintéticos. Não insira dados reais de pessoas ou empresas.
