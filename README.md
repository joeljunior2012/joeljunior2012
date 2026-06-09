# Alert System (Base da Fase 1)

Projeto inicial para sistema de **alertas** (sem compra/venda automática), focado em segurança e aprendizado.

## O que esta fase entrega

- Estrutura limpa de pastas.
- Configuração por variáveis de ambiente.
- Logger básico (console + arquivo).
- Inicialização mínima para validar ambiente.

> **Importante:** ainda **não** existe análise de mercado e **não** existe resposta automática.

## Estrutura do projeto

```text
.
├── .env.example
├── main.py
├── README.md
├── requirements.txt
├── src/
│   ├── config.py
│   └── logger_setup.py
├── logs/
├── data/
└── tests/
```

## Pré-requisitos (Windows)

- Windows 10/11
- Python 3.11+ instalado
- PowerShell (ou Prompt de Comando)

## Instalação no Windows (PowerShell)

1. Clone ou abra a pasta do projeto.
2. Crie ambiente virtual:

```powershell
python -m venv .venv
```

3. Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Instale dependências:

```powershell
pip install -r requirements.txt
```

5. Crie seu `.env` a partir do exemplo:

```powershell
copy .env.example .env
```

6. Edite o arquivo `.env` e ajuste os valores (principalmente Gmail e destino dos alertas).

## Como rodar

```powershell
python main.py
```

Você deverá ver logs no console e no arquivo `logs/app.log`.

## Segurança e boas práticas

- Mantenha `APP_MODE=TEST` durante desenvolvimento.
- Nunca commite o arquivo `.env` com credenciais reais.
- Use senha de app do Gmail (não use senha normal da conta).


## Fase 2 (envio de e-mail)

Nesta fase foi adicionado apenas o **envio de e-mail** via Gmail SMTP:

- Função `enviar_email()` no serviço `src/email_service.py`.
- Leitura segura de variáveis via `src/config.py`.
- `APP_MODE=TEST` simula envio e evita disparo real acidental.
- Logs de sucesso/erro no console e no arquivo de log.
- Tratamento de erro para autenticação e falhas SMTP.

### Como testar sem enviar e-mail real

Mantenha no `.env`:

```env
APP_MODE=TEST
```

Depois execute:

```powershell
python main.py
```

Você verá no log uma mensagem de simulação `[TEST MODE]`.

### Como testar envio real (quando quiser)

1. Configure no `.env` `APP_MODE=REAL`.
2. Preencha `SMTP_USER`, `SMTP_APP_PASSWORD` e `ALERT_EMAIL_TO`.
3. Rode `python main.py`.

> Observação: ainda não há leitura de caixa de entrada; somente envio.


## Fase 3 (leitura IMAP + processamento)

Nesta fase foi adicionado:

- Leitura de e-mails recebidos no Gmail via IMAP (`imap.gmail.com`).
- Filtro por palavras-chave.
- Classificação simples de prioridade (`ALTA`, `MEDIA`, `BAIXA`).
- Deduplicação por `Message-ID` para evitar resposta duplicada.
- Modo `TEST` mostrando resposta no log sem envio real.
- Histórico de e-mails processados em `data/processed_emails.jsonl`.

### Observações importantes

- Ainda não há análise de mercado.
- O foco aqui é somente pipeline de e-mail (entrada + resposta controlada).
- Em `TEST`, nenhuma resposta real é enviada.

### Execução

```powershell
python main.py
```


## Fase 4 (monitoramento de mercado)

Nesta fase foi adicionado monitoramento simples de mercado (sem indicadores avançados):

- Ativos monitorados: **BTC, ETH, SOL, BNB, XRP**.
- Preço em **USD** e **BRL**.
- Variação de **24h**.
- **Volume** de 24h.
- Alerta simples por e-mail quando `|variação 24h| >= 3%` (limiar inicial).

Fonte utilizada no código: API pública da CoinGecko (`/simple/price`).

### Execução

```powershell
python main.py
```

> Em `APP_MODE=TEST`, o envio de e-mail segue simulado via log.


## Fase 5 (indicadores + decisão de compra textual)

Indicadores adicionados (sem executar ordens):

- RSI
- Média Móvel Simples (SMA)
- Média Móvel Exponencial (EMA)
- Suporte
- Resistência
- Volatilidade
- Volume anormal

Também foi criada a função de decisão:

- **Comprar agora?** `Sim` / `Não` / `Aguardar confirmação`

As regras são simples e conservadoras, focadas em reduzir risco.

> Importante: o sistema **não executa ordens**; apenas calcula e registra a decisão em log.


## Fase 6 (melhor horário para operação)

Adicionada análise de timing operacional com foco em preservação de capital:

- Avaliação por **horário de Brasília**.
- Contexto de **abertura dos EUA** e **fechamento dos EUA**.
- Heurística de **liquidez** e **volatilidade**.
- Bloqueio de **horários ruins** (ex.: madrugada).
- Bloqueio de **horários de notícia** (janela macro sensível).
- Recomendação final: **operar agora** ou **aguardar**.

A recomendação é apenas informativa (log), sem execução automática de ordens.


## Fase 7 (score, anti-FOMO, overtrading e relatório diário)

Adicionado:

- **Score final de oportunidade (0 a 100)**.
- **Filtro anti-FOMO** (bloqueio de entradas esticadas).
- **Proteção contra overtrading** (limite diário de sinais).
- **Confiança do sinal** (`Alta`, `Média`, `Baixa`).
- **Histórico de sinais enviados** em `data/signals_history.jsonl`.
- **Relatório diário por e-mail** com resumo dos sinais do dia.

A lógica continua somente de recomendação/alerta, sem execução automática de ordens.
