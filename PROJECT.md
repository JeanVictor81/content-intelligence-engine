# Content Intelligence Engine
## Documento de visão, arquitetura e desenvolvimento

**Status:** especificação inicial da V1  
**Repositório:** `content-intelligence-engine`  
**Objetivo deste documento:** manter a visão do produto, as decisões técnicas e os limites de escopo alinhados durante o desenvolvimento.

---

## 1. Visão do projeto

O **Content Intelligence Engine** é uma aplicação que pesquisa conteúdos sobre um tema, organiza as informações encontradas, identifica assuntos em destaque, apresenta evidências e ajuda a transformar informações verificáveis em roteiros para conteúdo digital.

O produto não deve ser apenas um gerador de textos por IA. Seu diferencial é conectar **pesquisa, organização, análise, rastreabilidade das fontes e produção de conteúdo** em um fluxo consistente.

A primeira versão será desenvolvida para uso próprio, com arquitetura modular que permita evoluir futuramente para uma aplicação desktop, uma plataforma de produção de conteúdo e, eventualmente, um produto SaaS.

## 2. Objetivo da V1

A V1 deve cumprir um fluxo simples e útil:

1. O usuário informa um tema ou palavra-chave.
2. O sistema pesquisa fontes disponíveis.
3. O sistema coleta e normaliza os resultados permitidos.
4. Conteúdos duplicados ou muito semelhantes são identificados.
5. O sistema agrupa conteúdos em tópicos.
6. O sistema calcula um indicador de tendência transparente.
7. A IA analisa os conteúdos com referências às fontes.
8. O sistema apresenta fatos, alegações, opiniões e informações não confirmadas separadamente.
9. O usuário escolhe um tópico e solicita a geração de um roteiro.
10. O roteiro mantém referências às fontes que sustentam suas afirmações.

**Fora do escopo da V1:** geração de áudio, geração/edição de vídeo, publicação automática em redes sociais, análise de desempenho de publicações, monetização e integração com afiliados.

## 3. Exemplo de utilização

O usuário pesquisa `CBLOL`.

O sistema consulta fontes disponíveis e organiza os resultados por assunto, por exemplo:

- Resultado de uma partida;
- Mudança em uma equipe;
- Declaração de um jogador;
- Atualização de campeonato;
- Discussão relevante da comunidade.

Para cada tópico, a aplicação poderá apresentar:

- Título e resumo;
- Quando o assunto surgiu e quando as fontes foram publicadas;
- Plataformas e fontes encontradas;
- Quantidade de fontes independentes identificadas;
- Trend Score e explicação dos sinais que contribuíram para ele;
- Confidence Score e explicação da confiança nas informações;
- Fatos, alegações, opiniões e pontos ainda não confirmados;
- Divergências entre as fontes;
- Ação para gerar um roteiro.

Os tópicos e pontuações exibidos neste exemplo são ilustrativos. O sistema não deve inventar métricas de engajamento ou tratar uma pontuação como prova de veracidade.

## 4. Princípios fundamentais

### 4.1 Fonte antes da IA

A IA deve trabalhar sobre conteúdos recuperados e registrados. Não deve inventar fontes, links, citações, datas, estatísticas ou acontecimentos para preencher lacunas.

### 4.2 Rastreabilidade

Afirmações relevantes devem poder ser relacionadas às fontes que as sustentam. Sempre que possível, guardar URL, título, plataforma, autor, data de publicação e data de coleta.

### 4.3 Separação dos tipos de informação

O sistema deve distinguir claramente:

- **FACT:** informação sustentada por evidência confiável disponível;
- **CLAIM:** afirmação feita por uma pessoa, organização ou publicação, ainda que não esteja independentemente confirmada;
- **OPINION:** interpretação, avaliação ou opinião atribuída a alguém;
- **UNCONFIRMED:** informação para a qual a evidência disponível não permite confirmação suficiente.

Essas categorias são rótulos operacionais, não garantias absolutas. A aplicação deve mostrar a evidência e o contexto para que o usuário possa avaliar.

### 4.4 Neutralidade e contexto

Evitar sensacionalismo, títulos enganosos e conclusões mais fortes do que as fontes permitem. Quando houver versões conflitantes, mostrar a divergência e a incerteza em vez de escolher arbitrariamente uma versão.

### 4.5 Popularidade não é importância

Um tema pode apresentar muitos sinais de atenção sem ser necessariamente importante, verdadeiro ou relevante para todos os públicos. O Trend Score mede sinais observáveis de atenção, não a qualidade ou a veracidade do assunto.

### 4.6 Modularidade sem complexidade prematura

Cada responsabilidade deve ficar em um módulo claro. A V1 deve preferir serviços simples e testáveis a uma arquitetura distribuída, agentes autônomos ou infraestrutura complexa sem necessidade comprovada.

## 5. Trend Score

O **Trend Score** é um indicador de 0 a 100 para resumir sinais observáveis de atenção sobre um tópico.

Sinais possíveis:

- Recência das publicações;
- Crescimento da quantidade de menções, quando houver dados comparáveis;
- Número de fontes;
- Diversidade de fontes e plataformas;
- Frequência de publicação;
- Engajamento, somente quando a fonte fornecer dados confiáveis e comparáveis;
- Persistência do assunto ao longo do tempo;
- Relevância em relação ao tema pesquisado.

A primeira versão deve usar uma fórmula simples, explicável e configurável. Não incluir um sinal quando não houver dados suficientes; indicar a ausência de dados em vez de assumir um valor.

A interface deve mostrar os principais motivos da pontuação, por exemplo: “publicações recentes”, “encontrado em múltiplas fontes” ou “crescimento observado no período analisado”.

O score não deve ser apresentado como uma medição científica universal, nem comparado entre temas sem considerar diferenças de cobertura, plataforma e janela temporal.

## 6. Confidence Score

O **Confidence Score** é separado do Trend Score. Ele representa o nível de sustentação das informações de um tópico com base nas evidências disponíveis.

Sinais possíveis:

- Quantidade de fontes independentes;
- Autoridade e proximidade da fonte em relação ao acontecimento;
- Consistência entre fontes;
- Confirmação por fonte oficial, quando pertinente;
- Presença de contradições;
- Atualidade da informação;
- Clareza sobre a origem da afirmação.

A pontuação deve ser acompanhada de explicação e limitações. Uma fonte oficial pode confirmar o que uma organização declarou, mas isso não significa automaticamente que toda interpretação ou alegação associada esteja comprovada.

## 7. Arquitetura inicial

Fluxo principal:

`User Topic → Research Engine → Source Connectors → Normalization Engine → Deduplication Engine → Topic Extraction → Trend Engine → Analysis Engine → Script Engine`

Responsabilidades:

- **API:** recebe solicitações e entrega resultados;
- **Research Engine:** coordena a pesquisa;
- **Connectors:** integram fontes específicas;
- **Normalization Engine:** converte resultados para um formato comum;
- **Deduplication Engine:** identifica conteúdo repetido ou semelhante;
- **Topic Extraction:** agrupa conteúdos relacionados;
- **Trend Engine:** calcula sinais e Trend Score;
- **Analysis Engine:** organiza evidências, fatos, alegações e divergências;
- **Script Engine:** transforma a análise em roteiro com rastreabilidade;
- **Database:** armazena fontes, conteúdos, tópicos, análises e roteiros.

A aplicação pode começar com um backend/API e uma interface simples. A experiência desktop poderá ser adicionada depois, sem obrigar a reescrever a lógica central.

## 8. Stack inicial

### Backend

- Python;
- FastAPI;
- Pydantic;
- SQLAlchemy;
- PostgreSQL;
- Cliente de API para o provedor de IA escolhido.

### IA

A V1 deve implementar apenas o provedor efetivamente necessário. A integração deve ficar atrás de uma interface comum, para evitar dependência excessiva de um fornecedor.

Interface futura sugerida: `LLMProvider`, com implementações como `GeminiProvider`, `OpenAIProvider`, `ClaudeProvider` ou `LocalProvider`. Não é necessário implementar todos esses provedores na V1.

### Frontend futuro

- React;
- TypeScript;
- Tauri para empacotamento desktop, quando a interface web estiver estável.

### Infraestrutura

- Git e GitHub para versionamento;
- Docker Compose para ambiente local quando necessário;
- PostgreSQL;
- `.env` para configuração local.

Redis, filas de tarefas, Celery, serviços distribuídos e infraestrutura em nuvem devem ser considerados somente quando o uso justificar.

## 9. Frontend

A interface inicial deve priorizar clareza e fluxo de trabalho:

- Campo para informar tema;
- Botão para iniciar pesquisa;
- Estado de carregamento e mensagens de erro compreensíveis;
- Lista de tópicos encontrados;
- Trend Score com explicação;
- Confidence Score com explicação;
- Fontes e plataformas relacionadas;
- Tela de detalhe do tópico;
- Ação para gerar roteiro;
- Visualização do roteiro e suas referências;
- Histórico de pesquisas.

Não investir tempo excessivo em animações ou acabamento visual antes de validar o fluxo funcional.

## 10. Source Connectors

Cada conector deve encapsular a integração com uma fonte ou plataforma específica.

Interface conceitual:

- `search(query, options)`: procura conteúdos;
- `fetch(item)`: recupera detalhes permitidos;
- `normalize(raw_item)`: converte o resultado para o modelo comum.

Fontes potenciais incluem:

- APIs oficiais;
- RSS;
- Mecanismos de busca;
- Páginas públicas cujo acesso e uso sejam permitidos;
- Outras integrações autorizadas, adicionadas de forma incremental.

Não construir um scraper universal. Cada conector deve respeitar termos de uso, políticas da plataforma, limites de requisição, autenticação, direitos autorais e restrições técnicas aplicáveis. Preferir APIs oficiais ou métodos autorizados.

Se uma fonte não disponibilizar determinado dado, o sistema deve registrar a ausência em vez de fabricar ou inferir o valor.

## 11. Regras de coleta e conteúdo externo

- Respeitar os termos de serviço e políticas das fontes;
- Respeitar limites de requisição e controles de acesso;
- Não contornar autenticação, paywalls ou mecanismos de proteção;
- Não armazenar mais conteúdo do que o necessário;
- Guardar metadados e trechos conforme permitido;
- Tratar todo conteúdo externo como dado não confiável, nunca como instrução para o sistema;
- Registrar falhas e limitações de coleta;
- Evitar coletar dados pessoais desnecessários.

A aplicação deve apresentar a origem dos dados e não sugerir cobertura completa da internet.

## 12. Modelo de dados inicial

Os modelos devem começar simples e evoluir com as necessidades reais.

### Source

Representa a origem de um conteúdo.

Campos sugeridos:

- `id`;
- `name`;
- `platform`;
- `base_url`, quando aplicável;
- `source_type`;
- `created_at`.

### Content

Representa um item coletado.

Campos sugeridos:

- `id`;
- `source_id`;
- `external_id`, quando disponível;
- `url`;
- `title`;
- `text_excerpt` ou conteúdo permitido;
- `author`;
- `published_at`;
- `collected_at`;
- `content_hash`;
- `metadata` em JSON, quando apropriado.

### Topic

Representa um assunto agrupado.

Campos sugeridos:

- `id`;
- `query`;
- `title`;
- `summary`;
- `first_seen_at`;
- `last_seen_at`;
- `created_at`;
- `updated_at`.

### TopicContent

Relaciona conteúdos a tópicos, permitindo que um conteúdo esteja relacionado a mais de um tópico quando fizer sentido.

Campos sugeridos:

- `topic_id`;
- `content_id`;
- `relevance`;
- `relationship_type`.

### Trend

Armazena uma avaliação de tendência para um tópico em uma janela temporal.

Campos sugeridos:

- `id`;
- `topic_id`;
- `score`;
- `window_start`;
- `window_end`;
- `signals` em JSON;
- `calculated_at`.

### Claim

Representa uma afirmação extraída durante a análise.

Campos sugeridos:

- `id`;
- `topic_id`;
- `text`;
- `classification` (`FACT`, `CLAIM`, `OPINION`, `UNCONFIRMED`);
- `confidence_score`, quando calculado;
- `created_at`.

Uma relação adicional deve conectar afirmações às fontes que as sustentam, contradizem ou contextualizam.

### Script

Representa um roteiro gerado.

Campos sugeridos:

- `id`;
- `topic_id`;
- `title`;
- `body` ou blocos estruturados;
- `style`;
- `created_at`;
- `model_provider`, quando disponível;
- `model_name`, quando disponível.

Cada bloco do roteiro deve poder manter referências às afirmações ou fontes correspondentes.

## 13. Research Engine

O Research Engine coordena a pesquisa de um tema.

Fluxo esperado:

1. Validar e normalizar a consulta do usuário;
2. Selecionar os conectores habilitados;
3. Executar pesquisas respeitando limites e timeouts;
4. Registrar fontes, URLs e horários de coleta;
5. Converter resultados para o modelo interno;
6. Encaminhar os conteúdos para deduplicação;
7. Persistir os resultados;
8. Retornar um resumo do que foi encontrado e das limitações.

O mecanismo deve tratar falhas parciais: a indisponibilidade de um conector não deve necessariamente cancelar toda a pesquisa.

## 14. Normalization Engine

O Normalization Engine converte os resultados heterogêneos para uma estrutura comum.

Campos normalizados esperados:

- Identificador interno;
- Fonte e plataforma;
- URL;
- Título;
- Texto ou trecho permitido;
- Autor, se disponível;
- Data de publicação, se disponível;
- Data de coleta;
- Métricas disponibilizadas pela fonte;
- Metadados específicos da origem.

Os valores ausentes devem permanecer ausentes. Não preencher datas, autores, visualizações ou engajamento por suposição.

## 15. Deduplication Engine

O Deduplication Engine identifica itens repetidos ou muito semelhantes, sem apagar a procedência.

Sinais possíveis:

- URL canônica;
- Identificador externo;
- Hash do conteúdo normalizado;
- Similaridade de título e texto;
- Entidades citadas;
- Datas e contexto.

A deduplicação deve preservar todas as fontes relacionadas. Uma notícia reproduzida por vários sites não deve ser automaticamente tratada como várias confirmações independentes. Quando a independência não puder ser estabelecida, registrar essa limitação.

## 16. Topic Extraction

O Topic Extraction agrupa conteúdos que tratam do mesmo acontecimento ou assunto.

A IA pode auxiliar na identificação de:

- Tópicos;
- Títulos concisos;
- Resumos;
- Entidades;
- Relações entre conteúdos.

O sistema deve evitar fragmentar um mesmo acontecimento em vários tópicos quase idênticos. Agrupamentos automatizados devem manter vínculos com os conteúdos originais para revisão.

## 17. Trend Engine

O Trend Engine calcula sinais de atenção para cada tópico.

A primeira versão deve:

- Definir uma janela temporal explícita;
- Calcular apenas sinais sustentados por dados disponíveis;
- Explicar os componentes do score;
- Distinguir ausência de dados de valor zero;
- Permitir recalcular o score;
- Guardar o momento e a janela da avaliação.

O resultado deve ser interpretável e não deve afirmar que um tópico é “viral” sem critério operacional explícito.

## 18. Analysis Engine

O Analysis Engine organiza o que as fontes dizem sobre um tópico.

A análise pode conter:

- Resumo;
- O que aconteceu, segundo as fontes;
- Quando aconteceu e quando foi publicado;
- Pessoas, organizações e eventos envolvidos;
- Fatos sustentados;
- Alegações atribuídas;
- Opiniões atribuídas;
- Informações não confirmadas;
- Contexto relevante;
- Divergências entre fontes;
- Lacunas e limitações;
- Referências utilizadas.

A IA deve ser instruída a não completar lacunas com conhecimento não presente nas fontes recuperadas. Quando a evidência for insuficiente, deve declarar isso.

## 19. Source Comparison

Quando as fontes apresentarem informações divergentes:

1. Identificar exatamente quais afirmações divergem;
2. Mostrar quais fontes sustentam cada versão;
3. Registrar datas e contexto das publicações;
4. Considerar se uma fonte está citando outra;
5. Apresentar o que permanece incerto.

Não escolher uma versão apenas por ser mais repetida. A aplicação pode indicar fontes oficiais ou primárias, mas deve explicar o alcance da confirmação e não transformar isso em certeza além da evidência.

## 20. Script Engine

O Script Engine transforma a análise de um tópico em roteiro de vídeo curto.

Estrutura inicial sugerida:

1. **HOOK:** abertura que desperte interesse sem distorcer o acontecimento;
2. **CONTEXTO:** informação necessária para entender o assunto;
3. **DESENVOLVIMENTO:** fatos e detalhes relevantes;
4. **INFORMAÇÃO PRINCIPAL:** ponto central sustentado pelas fontes;
5. **CONCLUSÃO:** fechamento proporcional às evidências, sem inventar uma resolução.

O roteiro deve ser claro, natural e adequado à duração solicitada. O sistema não deve inventar falas, acontecimentos, números, citações ou conclusões para tornar o roteiro mais dramático.

## 21. Fontes no roteiro

Cada bloco ou afirmação factual relevante do roteiro deve manter referências internas às fontes de suporte.

Na interface, o usuário deve conseguir identificar:

- Qual fonte sustenta a afirmação;
- Se a fonte é primária ou secundária, quando conhecido;
- Se há fontes que contradizem ou limitam a afirmação;
- Se a informação é alegação, opinião ou não confirmada.

As referências não precisam interromper a narração, mas devem estar acessíveis para conferência e revisão antes da publicação.

## 22. Interface da V1

A V1 deve conter, no mínimo:

### Tela de pesquisa

- Campo de tema;
- Botão de pesquisa;
- Indicação de progresso;
- Erros e limitações de fontes.

### Lista de tópicos

- Título;
- Resumo curto;
- Trend Score;
- Confidence Score;
- Data/intervalo observado;
- Quantidade e diversidade de fontes, quando disponíveis.

### Detalhe do tópico

- Resumo e contexto;
- Fatos, alegações, opiniões e informações não confirmadas;
- Fontes relacionadas;
- Divergências;
- Sinais do Trend Score;
- Explicação do Confidence Score;
- Botão para gerar roteiro.

### Roteiro

- Texto organizado por blocos;
- Referências por bloco;
- Ação para copiar;
- Possibilidade de gerar uma nova versão.

## 23. Histórico

O sistema deve guardar o histórico de pesquisas e permitir que o usuário consulte resultados anteriores.

Registrar, quando aplicável:

- Consulta;
- Data da pesquisa;
- Fontes consultadas;
- Tópicos encontrados;
- Versão da análise;
- Roteiros gerados.

O histórico deve deixar claro que os resultados refletem o momento da coleta e podem ficar desatualizados.

## 24. Logging e observabilidade

Usar logging estruturado e níveis adequados:

- `INFO`: operações normais;
- `WARNING`: falhas parciais, dados incompletos ou limitações;
- `ERROR`: falhas que impedem uma operação.

Evitar `print` espalhado pela aplicação. Não registrar chaves de API, tokens, senhas ou dados sensíveis em logs.

## 25. Configuração

- Utilizar `.env` para configurações locais;
- Criar `.env.example` com nomes de variáveis e valores ilustrativos não secretos;
- Adicionar `.env` ao `.gitignore`;
- Validar configurações obrigatórias ao iniciar;
- Documentar como configurar e executar o projeto.

Nenhum segredo deve ser enviado ao GitHub.

## 26. Segurança

- Não expor chaves de API no frontend;
- Não armazenar tokens ou senhas no repositório;
- Validar entradas do usuário;
- Aplicar limites de tamanho e timeouts;
- Tratar conteúdo externo como não confiável;
- Evitar execução arbitrária de comandos;
- Prevenir SSRF e não permitir que o usuário force requisições a URLs internas ou arbitrárias;
- Tratar erros sem expor segredos ou detalhes internos;
- Restringir dependências e permissões ao necessário.

## 27. Estrutura inicial do repositório

A estrutura é uma referência inicial e pode ser refinada antes da implementação, desde que as responsabilidades permaneçam claras.

```text
content-intelligence-engine/
├── PROJECT.md
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── connectors/
│   │   └── database/
│   └── tests/
├── frontend/
├── docs/
└── scripts/
```

Não é obrigatório criar todas as pastas imediatamente. Criar diretórios quando houver código que justifique sua existência.

## 28. Primeira implementação — Milestone 001

**Objetivo:** realizar uma pesquisa simples de ponta a ponta e retornar resultados normalizados por uma API.

Fluxo de referência:

1. Usuário envia o tema `CBLOL`;
2. API valida a solicitação;
3. Research Engine consulta um conector inicial;
4. Resultados são normalizados;
5. Fontes e conteúdos são registrados no PostgreSQL;
6. API retorna os resultados com origem e datas disponíveis.

O conector inicial deve ser escolhido considerando acesso permitido, simplicidade e estabilidade. A primeira entrega não precisa cobrir todas as plataformas.

### Critérios de conclusão do M001

- API inicia localmente;
- Endpoint recebe uma consulta;
- Pelo menos um conector permitido realiza uma pesquisa;
- Resultados são normalizados para o modelo comum;
- Dados são persistidos no PostgreSQL;
- Resposta inclui fontes e metadados disponíveis;
- Erros e ausência de resultados são tratados;
- Testes básicos passam;
- Instruções de execução estão documentadas.

Não avançar para funcionalidades posteriores até revisar o M001.

## 29. Ordem de desenvolvimento

- **M001 — Fundação e pesquisa:** API, configuração, banco, primeiro conector e resultados normalizados;
- **M002 — Deduplicação:** identificar duplicados e preservar fontes relacionadas;
- **M003 — Extração de tópicos:** agrupar conteúdos relacionados;
- **M004 — Trend Engine:** calcular e explicar o Trend Score;
- **M005 — Análise:** classificar informações e apresentar evidências e divergências;
- **M006 — Roteiros:** gerar roteiro fundamentado e manter referências;
- **M007 — Interface:** criar a experiência de pesquisa e consulta, caso não tenha sido feita antes como interface mínima de validação.

A ordem pode ser ajustada por dependências técnicas, mas cada alteração deve ser justificada e aprovada antes de ampliar o escopo.

## 30. Funcionalidades futuras

As funcionalidades abaixo não fazem parte da V1:

- **V2:** títulos, descrições, legendas e hashtags;
- **V3:** geração de voz por TTS, incluindo integração opcional com ElevenLabs;
- **V4:** imagens, vídeos, edição, legendas automáticas, thumbnails e integração com FFmpeg;
- **V5:** publicação ou agendamento em TikTok, YouTube, Instagram e Kwai, conforme APIs e permissões disponíveis;
- **V6:** métricas e análise de desempenho dos conteúdos publicados;
- **V7:** integração com mecanismo de ofertas e afiliados;
- **V8:** evolução para SaaS multiusuário.

Essas etapas devem ser reavaliadas com base no aprendizado da versão anterior, nas políticas das plataformas e nos custos operacionais.

## 31. Integração futura com Affiliate Engine

A visão de longo prazo pode conectar o Content Intelligence Engine a um mecanismo de afiliados:

`Content Intelligence Engine → Content Engine + Affiliate Engine`

O Content Intelligence Engine identifica temas e organiza evidências. O Content Engine apoia a produção e distribuição. O Affiliate Engine poderá localizar e organizar ofertas compatíveis com conteúdos, com transparência sobre relações comerciais.

Essa integração deve ser desacoplada. Não permitir que interesses de monetização alterem fatos, fontes, classificações ou conclusões da análise.

## 32. Integração futura com múltiplas IAs

A arquitetura deve permitir trocar ou combinar provedores de modelos sem reescrever a lógica de negócio.

A abstração `LLMProvider` poderá padronizar tarefas como:

- Extração de tópicos;
- Resumo;
- Classificação de afirmações;
- Comparação de fontes;
- Geração de roteiros.

A V1 deve implementar apenas o necessário. Comparações entre provedores, roteamento inteligente, fallback automático e modelos locais ficam para uma etapa futura, quando houver testes e critérios claros de qualidade, custo, privacidade e latência.

## 33. Regra para agentes de IA

Agentes podem ser úteis futuramente para tarefas bem delimitadas, mas a V1 não deve depender de um sistema complexo de agentes autônomos.

Priorizar serviços explícitos, funções previsíveis, entradas e saídas tipadas, logs e testes. Se agentes forem adicionados, devem operar com permissões limitadas, ferramentas autorizadas e validação das saídas.

## 34. Princípio de desenvolvimento

Ordem de prioridade:

1. Funcionar;
2. Estar correto e rastreável;
3. Ser testado;
4. Ser simples de manter;
5. Ser eficiente;
6. Ser visualmente refinado.

Evitar construir infraestrutura para problemas que ainda não existem. Cada componente deve resolver uma necessidade identificada.

## 35. Testes

Criar testes automatizados para:

- Validação de entrada;
- Conectores e tratamento de falhas;
- Normalização;
- Deduplicação;
- Extração e agrupamento de tópicos;
- Cálculo do Trend Score;
- Classificação de afirmações;
- Tratamento de divergências;
- Geração de roteiros e referências;
- Persistência e endpoints da API.

Usar dados de teste reproduzíveis e evitar que testes unitários dependam de serviços externos ou chaves reais. Testes de integração com APIs externas devem ser separados e explicitamente configurados.

## 36. Critério de sucesso da V1

A V1 será considerada funcional quando o usuário conseguir:

1. Abrir a aplicação ou acessar sua interface local;
2. Informar um tema;
3. Executar uma pesquisa;
4. Receber conteúdos de fontes identificáveis;
5. Visualizar tópicos organizados;
6. Consultar o Trend Score e entender os sinais que o compõem;
7. Abrir um tópico e consultar a análise;
8. Ver fatos, alegações, opiniões e informações não confirmadas separados;
9. Conferir as fontes e eventuais divergências;
10. Gerar um roteiro com referências às fontes utilizadas.

O objetivo é validar a utilidade do ciclo de pesquisa e transformação, não a quantidade de plataformas integradas.

## 37. Regra de ouro

**DISCOVER → ORGANIZE → VERIFY → UNDERSTAND → TRANSFORM**

O produto deve descobrir informações, organizá-las, facilitar a verificação, apoiar a compreensão e só então transformá-las em conteúdo.

A qualidade e a rastreabilidade da informação são mais importantes do que produzir um roteiro rapidamente.

## 38. Estado atual do projeto

- Repositório GitHub criado: `JeanVictor81/content-intelligence-engine`;
- Branch principal: `main`;
- Repositório clonado localmente em `C:\Users\Mago\Desktop\content-intelligence-engine`;
- Estado inicial conhecido: `README.md` mínimo e repositório Git;
- Próxima etapa: revisar esta especificação, preparar o ambiente de desenvolvimento e planejar o Milestone 001.

Não presumir que ferramentas como Python, Node.js, Docker, WSL ou PostgreSQL estejam instaladas. Confirmar o estado do ambiente antes de iniciar a implementação.

## 39. Instruções para o Cursor

Ao trabalhar neste repositório:

- Ler este `PROJECT.md` antes de propor ou realizar alterações;
- Respeitar o escopo da etapa atual;
- Não implementar funcionalidades futuras sem solicitação;
- Não alterar a arquitetura sem explicar o motivo, os impactos e as alternativas;
- Preferir código modular, simples, tipado quando aplicável e testável;
- Manter a rastreabilidade entre conteúdo, afirmações e fontes;
- Não tratar saídas de IA como verdade sem evidência;
- Não inventar dados ausentes;
- Não adicionar segredos ao repositório;
- Atualizar documentação quando decisões ou comandos mudarem;
- Apresentar um plano pequeno antes de implementações relevantes;
- Executar testes apropriados após alterações e relatar os resultados;
- Não fazer commit ou push sem autorização explícita;
- Não instalar ferramentas nem executar ações destrutivas sem autorização;
- Pedir confirmação antes de decisões arquiteturais importantes.

## 40. Primeira tarefa do Cursor

A primeira tarefa após adicionar este arquivo ao repositório é **análise e planejamento, sem implementação**.

Solicitação ao Cursor:

1. Leia o `PROJECT.md` completo;
2. Inspecione a estrutura atual do repositório;
3. Analise o Milestone 001;
4. Identifique dependências, riscos, decisões ainda abertas e possíveis problemas na arquitetura proposta;
5. Sugira a estrutura mínima de arquivos necessária para o M001;
6. Apresente um plano incremental, com entregas pequenas e verificáveis;
7. Indique quais ferramentas precisam ser instaladas e por quê, sem instalá-las;
8. Não implemente o M001 ainda;
9. Não avance para o M002;
10. Não faça commit ou push.

Ao final, aguarde a revisão e autorização do usuário antes de iniciar a implementação.
