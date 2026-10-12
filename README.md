# Sistema de alertas de e-mail e criptomoedas

Aplicação Python de **apoio à decisão**, com Gmail (SMTP/IMAP), monitoramento de BTC, ETH, SOL, BNB e XRP, indicadores técnicos, timing, score e gestão de risco.

> **Segurança:** o projeto não compra, não vende, não usa alavancagem e não se conecta a corretoras. Os alertas não são recomendação financeira e não prometem lucro.

## Recursos concluídos

- Modo `TEST` sem envio real de e-mail.
- SMTP Gmail com TLS, senha de app e limite horário anti-spam.
- IMAP opcional, palavras-chave, prioridade, deduplicação e marcação como lido.
- Preço USD/BRL, variação e volume via CoinGecko.
- RSI, SMA, EMA, suporte, resistência, volatilidade e volume anormal.
- Timing em horário de Brasília, score 0–100, confiança, anti-FOMO e overtrading.
- Stop obrigatório, alvo, risco/retorno e exposição máxima sugerida.
- Histórico JSONL, relatório diário opcional e execução única ou periódica.
- Backup ZIP com verificação de integridade, retenção e restauração segura.

## Estrutura

```text
main.py                    # orquestra um ciclo ou execução contínua
src/config.py              # lê e valida o .env
src/email_service.py       # envio SMTP e limite anti-spam
src/inbox_service.py       # leitura/processamento IMAP
src/market_service.py      # dados da CoinGecko
src/signal_service.py      # indicadores técnicos
src/risk_manager.py        # stop, alvo e risco/retorno
src/alert_formatter.py     # formato padronizado do alerta
src/timing_service.py      # filtro de horário
src/opportunity_service.py # score, confiança e disciplina
src/report_service.py      # resumo diário
src/backup_service.py      # backup e restauração dos históricos
tests/                     # testes sem internet
logs/ e data/              # arquivos gerados localmente
```

## Instalação no Windows (PowerShell)

### 1. Abrir o terminal na pasta correta

No Explorador de Arquivos, abra a pasta do projeto, clique na barra de endereço, digite `powershell` e pressione **Enter**. Confirme:

```powershell
dir
```

Você deve ver `main.py`, `requirements.txt` e a pasta `src`. Não copie caminhos de exemplo como `C:\caminho\para\...`.

### 2. Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

O MVP usa somente a biblioteca padrão do Python 3.11 ou superior; portanto o
arquivo é mantido como documentação e o comando não baixa pacotes externos.

### 4. Criar a configuração local

```powershell
Copy-Item .env.example .env
notepad .env
```

Comece com `APP_MODE=TEST`, `RUN_INBOX=false` e `SEND_DAILY_REPORT=false`. Assim, nenhum e-mail real será enviado.

### 5. Executar os testes

```powershell
python -m unittest discover -s tests -v
```

### 6. Fazer uma execução única

```powershell
python main.py
```

O programa consulta a API pública de mercado. Se estiver sem internet ou a API limitar requisições, ele registra o erro e encerra com segurança.

### 7. Executar continuamente

```powershell
python main.py --loop
```

O intervalo vem de `ANALYSIS_INTERVAL_MINUTES` e aceita 5, 15, 30 ou 60 minutos. Encerre com `Ctrl+C`.

## Gmail: configuração segura

1. Ative a verificação em duas etapas na Conta Google.
2. Crie uma **senha de app** para esta aplicação.
3. No `.env`, preencha `SMTP_USER`, `SMTP_APP_PASSWORD` e `ALERT_EMAIL_TO`.
4. Remova espaços da senha de app ao colá-la.
5. Só depois dos testes, altere `APP_MODE=REAL`.

Para ler a caixa de entrada, altere `RUN_INBOX=true`. Em modo real, respostas são enviadas ao remetente; o limite `MAX_EMAILS_PER_HOUR` reduz risco de spam. Faça primeiro um teste com uma conta dedicada.

## Agendar no Windows

Use o **Agendador de Tarefas**:

1. Escolha **Criar tarefa básica** e defina o horário.
2. Em **Programa/script**, selecione `C:\CAMINHO_REAL\DO_PROJETO\.venv\Scripts\python.exe`.
3. Em **Adicionar argumentos**, use `main.py` (ou `main.py --loop`).
4. Em **Iniciar em**, informe a pasta real do projeto.

Nunca use os textos `CAMINHO_REAL` literalmente: substitua pelo caminho exibido no Explorador de Arquivos.

## Limitações conhecidas

- Esta versão monitora somente as cinco criptomoedas listadas; dólar, índices, ouro, notícias, sentimento e dashboard visual permanecem como extensões futuras.
- As regras são heurísticas educativas, não modelos preditivos.
- Janelas macro são aproximadas e não substituem calendário econômico atualizado.
- APIs gratuitas podem ficar indisponíveis ou impor limites.

## Arquivos locais e privacidade

Não publique `.env`, logs ou históricos de e-mail. O `.gitignore` evita o versionamento desses arquivos, mas você continua responsável por proteger suas credenciais.

## Recuperação e backup dos dados

Os históricos atuais ficam em `data/*.jsonl`. Como esses arquivos são privados e
ignorados pelo Git, **não é possível recuperar dados perdidos numa formatação a
partir deste repositório**. Verifique antes se existe uma cópia no OneDrive,
Google Drive, backup do Windows, disco antigo ou Lixeira.

Para criar uma cópia manual:

```powershell
python main.py --backup
```

Para proteção contra outra formatação, configure no `.env` uma pasta que esteja
fora do disco local ou sincronizada. Use barras `/` no caminho:

```dotenv
BACKUP_ENABLED=true
BACKUP_DIR=C:/Users/SeuNome/OneDrive/AlertSystemBackups
BACKUP_RETENTION=30
```

Com `BACKUP_ENABLED=true`, cada ciclo concluído cria um ZIP. O ZIP não contém o
`.env` nem a senha do Gmail. Para restaurar uma cópia em uma instalação nova:

```powershell
python main.py --restore "C:/Users/SeuNome/OneDrive/AlertSystemBackups/alert-system-AAAA.zip"
```

Por segurança, arquivos existentes não são substituídos. Confira-os e, somente
se realmente quiser substituí-los, acrescente `--overwrite`:

```powershell
python main.py --restore "C:/caminho/backup.zip" --overwrite
```
