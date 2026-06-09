# Visão geral e plano incremental (sem codar tudo de uma vez)

Este documento consolida a visão geral do sistema de alertas e divide a execução em fases pequenas, com foco em segurança, rastreabilidade e aprendizado.

## Objetivo macro

Construir um sistema de apoio à decisão para cripto que:
- Gere apenas alertas e recomendações (sem execução de ordens).
- Priorize preservação de capital.
- Tenha modo TEST por padrão.
- Seja auditável por logs e históricos.
- Rode bem em Windows.

---

## Princípios de segurança (imutáveis)

1. **Sem auto-trade**: nenhuma ordem automática.
2. **TEST primeiro**: qualquer recurso novo nasce em modo teste.
3. **Logs completos**: tudo que decidir precisa ser explicável.
4. **Fail safe**: em erro de API/credencial/timezone, não operar.
5. **Proteção comportamental**: anti-FOMO e anti-overtrading.

---

## Fases menores (roadmap sugerido)

### Fase A — Base operacional mínima
- Estrutura de pastas.
- `.env.example` e validação de config.
- Logger em arquivo + console.
- `main.py` inicial.

**Saída:** app inicia e registra logs no Windows.

### Fase B — Canal de alerta (saída)
- Serviço SMTP Gmail.
- `enviar_email()` com tratamento de erro.
- TEST mode simulando envio.

**Saída:** alerta de teste com rastreabilidade.

### Fase C — Entrada de contexto por e-mail
- Leitura IMAP Gmail.
- Filtro por palavra-chave.
- Prioridade de e-mail.
- Deduplicação por `Message-ID`.

**Saída:** caixa processada com histórico local.

### Fase D — Dados de mercado
- Monitorar BTC, ETH, SOL, BNB, XRP.
- Preço USD/BRL, variação 24h, volume.
- Alerta simples por variação.

**Saída:** snapshot de mercado + alerta básico.

### Fase E — Sinais técnicos básicos
- RSI, SMA, EMA.
- Suporte/resistência.
- Volatilidade.
- Volume anormal.
- Função “Comprar agora? Sim/Não/Aguardar”.

**Saída:** decisão técnica explicável, sem execução.

### Fase F — Timing operacional
- Horário de Brasília.
- Abertura/fechamento EUA.
- Janela ruim e janela de notícia.
- Recomendação operar agora/aguardar.

**Saída:** filtro temporal para reduzir entradas ruins.

### Fase G — Score e disciplina
- Score final 0–100.
- Confiança do sinal.
- Anti-FOMO.
- Anti-overtrading (limite diário).
- Histórico de sinais enviados.

**Saída:** camada de disciplina e controle de risco comportamental.

### Fase H — Relatório diário
- Resumo diário por e-mail.
- Totais, média de score, sinais recentes.

**Saída:** visão executiva diária para revisão.

### Fase I — Hardening antes de produção
- Testes unitários por serviço.
- Testes de integração com mocks.
- Checklist operacional.
- Observabilidade e fallback.

**Saída:** operação assistida com risco controlado.

---

## Por onde começar agora (recomendação prática)

Comece pela **Fase A** e conclua 100% antes de avançar.

### Ordem exata recomendada
1. `config.py` + `.env.example`
2. `logger_setup.py`
3. `main.py` mínimo
4. teste local em Windows

### Critério de pronto da primeira etapa
- Rodar `python main.py` sem erro.
- Criar log em arquivo.
- Exibir `APP_MODE=TEST` no startup.

---

## Definição de sucesso do MVP

O MVP é considerado pronto quando conseguir:
- Coletar mercado,
- calcular sinais básicos,
- aplicar filtros de risco e timing,
- gerar alerta por e-mail,
- registrar histórico completo,
- sem executar ordens automaticamente.
