## Problema
- A seção "Visão Geral" está exibindo HTML como texto, indicando que `st.markdown(..., unsafe_allow_html=True)` não está renderizando como esperado no ambiente.
- Em projetos Streamlit, HTML complexo pode ser bloqueado ou renderizado de forma inconsistente.

## Opções de Correção
1. Substituir `st.markdown` por `st.components.v1.html(...)` para renderização completa do HTML.
2. Refatorar a UI para usar apenas componentes nativos do Streamlit (colunas, metric, texto), evitando HTML.

## Decisão
- Seguir o "padrão Streamlit" e refatorar para componentes nativos (Opção 2). Isso elimina problemas de renderização e mantém o projeto alinhado às melhores práticas.

## Implementação
### 1) Cálculo do período
- Reutilizar `mes_selecionado` já definido no topo e calcular `data_inicio` e `data_fim` do mês atual/selecionado.
- Garantir consistência de tipos `datetime` nas comparações com o DataFrame.

### 2) KPIs do topo (card)
- Criar um container e três colunas (`st.columns(3)`):
  - Coluna 1: `st.metric("Inicial", formatar_valor_br(saldo_inicial_total))`
  - Coluna 2: `st.metric("Saldo atual", formatar_valor_br(saldo_atual_total))`
  - Coluna 3: `st.metric("Previsto", formatar_valor_br(saldo_previsto))`
- Abaixo, inserir uma barra de progresso simples (`st.progress`) com percentual calculado como `saldo_atual_total / max(saldo_previsto, 1)` limitado a 0–1.

### 3) Lista "Visão Geral" sem HTML
- Renderizar quatro linhas usando `st.container()` e, para cada linha, `left, right = st.columns([3,1])`:
  - Linha Contas: esquerda `"🏛️ Contas"`, direita `formatar_valor_br(saldo_atual_total)`
  - Linha Receitas: esquerda `"➕ Receitas"`, direita `formatar_valor_br(receitas_periodo)`
  - Linha Despesas: esquerda `"➖ Despesas"`, direita `formatar_valor_br(despesas_periodo)`
  - Linha Balanço transferências: esquerda `"🔁 Balanço transferências"`, direita `formatar_valor_br(balanco_transferencias)`
- Separadores com `st.divider()` e títulos com `st.subheader("Visão geral")`.

### 4) Manter "Meus Cartões" intacto
- Não alterar a seção dos cartões.

### 5) Robustez e compatibilidade
- Remover todo HTML/CSS customizado da seção "Visão Geral".
- Garantir que as funções utilitárias chamadas (ex.: `calcular_saldo_anterior_com_inicial`) operem com `datetime` e que não ocorra `NameError`/`TypeError`.

### 6) Verificação
- Testar com mês selecionado e com "Todos os meses".
- Testar cenários: sem transações, apenas receitas, apenas despesas, com transferências.
- Verificar que nada é exibido como código; apenas componentes Streamlit.

## Entregáveis
- Atualização de `Dashboard.py` substituindo as duas chamadas `st.markdown` da Visão Geral por componentes nativos.
- Nenhuma alteração na seção "Meus Cartões".

## Confirmação
- Posso aplicar essa refatoração agora para deixar a "Visão Geral" 100% no padrão Streamlit?