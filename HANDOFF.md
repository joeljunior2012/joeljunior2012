# Resumo compacto para continuar o projeto em outra conversa

## Contexto e objetivo

O usuário é iniciante e pediu acompanhamento didático, por fases, para criar um
sistema Python que rode no Windows. O sistema deve ler e responder e-mails do
Gmail, monitorar criptomoedas e gerar alertas de apoio à decisão. A prioridade é
preservar capital, reduzir risco e evitar decisões emocionais.

Regras permanentes:

- nunca comprar ou vender automaticamente;
- nunca enviar ordens para corretoras;
- nunca prometer lucro ou usar alavancagem automática;
- usar `APP_MODE=TEST` antes do modo real;
- usar senha de app do Gmail, nunca a senha normal;
- manter logs, histórico e tratamento de erros;
- explicar os passos de forma simples para Windows.

## Estado atual

O MVP foi implementado e está organizado em serviços:

- `main.py`: execução única, loop, backup e restauração;
- `src/config.py`: leitura e validação do `.env`, somente com biblioteca padrão;
- `src/logger_setup.py`: logs no console e em `logs/app.log`;
- `src/email_service.py`: Gmail SMTP, TLS, modo TEST e limite anti-spam;
- `src/inbox_service.py`: Gmail IMAP, palavras-chave, prioridade e deduplicação;
- `src/market_service.py`: BTC, ETH, SOL, BNB e XRP via CoinGecko;
- `src/signal_service.py`: RSI, SMA, EMA, suporte, resistência, volatilidade e volume;
- `src/risk_manager.py`: stop, alvo, risco/retorno e exposição máxima;
- `src/timing_service.py`: heurísticas de horário de Brasília e sessão dos EUA;
- `src/opportunity_service.py`: score, confiança, anti-FOMO e overtrading;
- `src/alert_formatter.py`: formato textual padronizado dos alertas;
- `src/report_service.py`: resumo diário;
- `src/backup_service.py`: ZIP com manifesto, SHA-256, retenção e restauração segura.

O sistema usa apenas Python 3.11+ e não requer pacotes externos. O histórico é
gravado como JSONL em `data/`. Somente alertas enviados ou simulados entram no
histórico usado pelo controle de overtrading.

## Segurança e backup

O usuário informou que formatou a máquina e perdeu parte dos dados. Dados já
apagados não podem ser recuperados pelo Git porque `.env`, logs e `data/*.jsonl`
são privados e ignorados. Foi criado backup manual/automático. Para sobreviver a
outra formatação, `BACKUP_DIR` deve apontar para OneDrive, disco externo ou pasta
sincronizada, e não apenas para o disco local.

Comandos:

```powershell
python main.py --backup
python main.py --restore "C:/caminho/backup.zip"
python main.py --restore "C:/caminho/backup.zip" --overwrite
```

A restauração não sobrescreve arquivos existentes sem `--overwrite`.

## Como iniciar no Windows

Abra a pasta real do projeto no Explorador, digite `powershell` na barra de
endereço e execute:

```powershell
python --version
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
notepad .env
python -m unittest discover -s tests -v
python main.py
```

Configuração inicial segura:

```dotenv
APP_MODE=TEST
RUN_INBOX=false
RUN_MARKET=true
SEND_DAILY_REPORT=false
BACKUP_ENABLED=true
BACKUP_DIR=C:/Users/SEU_USUARIO/OneDrive/AlertSystemBackups
```

Para execução contínua:

```powershell
python main.py --loop
```

## Gmail

Ativar verificação em duas etapas, criar uma senha de app e preencher no `.env`:

```dotenv
SMTP_USER=seu_email@gmail.com
SMTP_APP_PASSWORD=sua_senha_de_app
ALERT_EMAIL_TO=destinatario@gmail.com
```

Primeiro manter `APP_MODE=TEST`. Depois de revisar as simulações por alguns dias,
alterar para `APP_MODE=REAL`. Ativar `RUN_INBOX=true` por último e,
preferencialmente, usando uma conta Gmail dedicada.

## Validação realizada

- compilação de `main.py`, módulos e testes;
- 13 testes unitários aprovados;
- inicialização offline com mercado e IMAP desativados;
- criação real de backup ZIP pelo CLI;
- árvore Git limpa após o commit anterior.

## Limitações conhecidas

- o MVP monitora somente BTC, ETH, SOL, BNB e XRP;
- dólar, S&P 500, Nasdaq, ouro, notícias, sentimento e dashboard visual ainda não
  foram implementados;
- regras técnicas e de horário são heurísticas educativas, não previsão de mercado;
- APIs gratuitas podem limitar ou interromper consultas;
- o usuário ainda precisa validar Gmail e execução real no próprio Windows.

## Próximo passo recomendado

Não adicionar recursos antes da validação local. Pedir ao usuário o resultado
exato destes dois comandos e resolver qualquer erro apresentado:

```powershell
python -m unittest discover -s tests -v
python main.py
```

Depois confirmar que `logs/app.log` e o backup no OneDrive foram criados. Somente
então testar SMTP real e, por último, IMAP.

## Git

O commit funcional anterior ao documento de handoff é:

```text
2f7c876 feat: finalize dependency-free alert MVP
```

Ao continuar em outra conversa, anexar este arquivo e informar qualquer mensagem
de erro completa, sem ocultar linhas. Nunca anexar `.env` nem senha de app.
