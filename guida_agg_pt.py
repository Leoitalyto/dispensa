# -*- coding: utf-8 -*-
"""Instruções atualizadas em 20/11/2026 — PORTUGUÊS (ver guida_aggiornamento.py)."""

ga_traduci("pt", {
    "x_campanello": ("🔔 O sininho: avisos desta secção", """Em cada secção, por baixo dos botões coloridos, há **🔔 Avisos desta secção**. Toque: uma janela diz **como os avisos estão configurados** e **o que está a vencer**.

Aí pode mudar:
- **Receber os avisos desta secção**: o interruptor liga-os ou desliga-os.
- **Quantos dias antes**: escolha os dias (0 = no próprio dia).
- **Escolho eu a hora**: marque, escolha a hora e carregue em **Enter** no teclado. Sem hora escolhida os avisos chegam de manhã.
- **Onde receber os avisos**: «como as outras secções» ou escolha entre **Telegram, Email, WhatsApp, SMS**.
- **Calendário**: ligue «Ver estes avisos também no calendário» e carregue em **Descarregar o calendário**; abra o ficheiro e o Android propõe o **Google Calendar**. Se uma data mudar, descarregue e abra outra vez (atualiza, não duplica).
- **Voltar como antes** repõe tudo.

Carregue em **💾 Guardar**. **Antes**, escreva os seus contactos (Telegram, email, WhatsApp, SMS) em **Saúde → Escolher como receber os avisos**: sem contacto esse canal não parte. Os avisos são enviados por um programa automático: às vezes com alguns minutos de atraso; uma mensagem falhada é recuperada em 3 horas, uma só vez.""",
                     "sininho avisos dias hora canais telegram email whatsapp sms som calendário google calendar"),
    "x_riuso_archivio": ("🗂️ Reutilizar um ficheiro que já está no arquivo", """Se já tem um ficheiro ou uma foto no arquivo **não precisa de os refazer**:
- **Saúde** (consultas, receitas, documentos, vacinas): por baixo de «tirar ou escolher um ficheiro» há **🗂️ Ou anexar do arquivo**. Escreva para procurar, escolha o ficheiro e guarde: usa-se o mesmo ficheiro, sem cópia.
- **Casa, Trabalho (recibos de vencimento), Carro, Animais**: no quadro onde carrega um ficheiro abra **🗂️ Ou escolher um ficheiro já no arquivo**, escolha e carregue em **📥 Usar este ficheiro**: é lido como se o tivesse acabado de carregar.
- **Despensa** (foto do produto): **🗂️ Escolher do arquivo** mostra as fotos já usadas, também de produtos acabados.""",
                         "arquivo reutilizar ficheiro foto já guardado escolher do arquivo anexar sem refazer"),
    "x_numeri_utili": ("📞 Números úteis e 📅 Consultas marcadas", """Em cada secção (exceto a Despensa), por baixo do sininho, há dois botões.

**📞 Números úteis** é a sua agenda de quem é preciso nessa secção: **nome, profissão, área, telefone do escritório e telemóvel, horários, site, email, morada**.
- Se há um trabalho, marque **«Há um orçamento»**: estado, valor, **datas de início e fim** e o **PDF ou foto do orçamento**.
- Em **«Documentos recebidos»** ponha PDF, fotos, faturas, contratos.
- Com **«Abrir orçamento, ficheiros e pagamentos»** regista **sinal, prestações e saldo** e vê quanto já pagou e quanto falta.
- Há também **Notas** e botões para ligar, WhatsApp, email, abrir o mapa ou o site.

**De quem são?** Em **Saúde, Os meus documentos e Casa**, onde se escolhe uma pessoa, números e consultas estão **separados por pessoa**.

**📅 Consultas marcadas**: **nome, função, data, hora, telefone, motivo e notas**. Em cima vê as **próximas**, por data; as passadas ou feitas ficam em baixo. Com **«Pôr no calendário do telefone»** a consulta entra no calendário com um lembrete.""",
                       "números úteis agenda consultas orçamento pagamentos sinal saldo contactos calendário"),
    "x_conti_casa": ("💶 Gestão das contas", """Em **Casa** toque em **💶 Gestão das contas**. Junte as entradas que quiser: **contas à ordem** (com o banco), **Postepay**, **cadernetas postais**, **BOT, BTP**, fundos, ações, certificados postais, dinheiro. Vê o **total** em cima e em baixo, os **subtotais** por tipo e um campo de **Notas**. Para os títulos do Estado pode anotar o vencimento. **Cada pessoa tem as suas contas**: se em Casa escolheu, por exemplo, a sua mãe, o botão passa a **«Contas de …»**. As contas de uma pessoa não se misturam com as dos outros.""",
                     "contas dinheiro banco conta à ordem postepay poupança obrigações btp bot total subtotal pessoa"),
    "x_badante": ("👵 Cuidadora (só administrador)", """Em **Casa**, só para o administrador, há **👵 Cuidadora**.
- Defina a **tarifa** (normalmente 20 € por 2 horas), os dias em que vem e a partir de que dia contar.
- Todos os dias toque em **✅ Veio** ou **❌ Não veio**; se o valor mudar use **«Outro dia ou outro valor»**.
- Com **«Dei dinheiro à minha mãe»** regista quanto e quando.
- A app calcula o que falta e **até quando chega o dinheiro**.
- **🔔 Avisos da cuidadora** avisa **3 dias antes** e **no último dia** (dias alteráveis).
- Há também **contactos da cuidadora** e **notas**.""",
                  "cuidadora badante horas tarifa veio dinheiro mãe avisos"),
    "x_interruttori": ("💡 Seletores tipo interruptor", """Em toda a app os seletores em pílula (para escolher pessoa, casa, veículo…) funcionam como **interruptores**: o **ativo é azul néon e pulsa**, os outros parecem **desligados**.""",
                       "interruptor seletor pílula ativo néon"),
    "x_ia": ("🤖 Inteligência artificial: documentos, manuscritos, luzes de aviso, línguas", """Com as **chaves** dos serviços de inteligência artificial (gratuitos: Groq, Google Gemini, OpenRouter, NVIDIA, Cloudflare, Cohere, Hugging Face, SambaNova com crédito de teste; **DeepSeek** pago, opcional) a app:
- **lê e classifica os documentos de saúde** (que documento é, área médica, exame, datas, médico, estrutura, conclusões). Se está **escrito à mão**, **vários serviços** leem-no e um «árbitro» compara as leituras: vê **quem o leu**, os **limites** e **o que verificar** na folha. Nada se guarda sem a sua confirmação;
- **reconhece as luzes de aviso do carro**, comparando várias leituras quando a foto é duvidosa;
- **traduz as páginas** para a língua escolhida (na primeira vez que uma página abre; depois fica guardado para todos);
- faz **o assistente** responder na língua escolhida.
Se um serviço estiver esgotado ou lento, a app passa sozinha ao seguinte.

**O DeepSeek é pago**: só o usam **o administrador** e as pessoas que ele escolhe (Utilidades → 🤖 → DeepSeek → **🔒 Quem pode usar**). Na mesma linha vê-se o **💰 crédito restante**. As traduções automáticas nunca usam serviços pagos.

O administrador coloca as chaves em **Utilidades → 🤖 Inteligência artificial**, com o guia passo a passo; **🔄 Voltar a verificar as chaves** e o **teste** de cada serviço dizem se funciona. Atenção: com as chaves gratuitas da Google os textos podem ser usados para melhorar os modelos deles.""",
             "inteligência artificial ia chaves gemini groq openrouter nvidia cloudflare cohere hugging face sambanova deepseek crédito quem pode usar manuscrito luzes tradução"),
    "x_compleanni": ("🎂 Aniversários: as fichas das pessoas", """Em **Utilidades → 🎂 Aniversários** toque no **emblema «Feliz aniversário»** para abrir a lista (toque outra vez para fechar).

- **➕ Adicionar uma pessoa**: nome e data de nascimento (se não sabe o ano marque **«Não sei o ano»**). O resto é opcional: **foto, local de nascimento, apelido, alcunha, telemóvel, telefone, WhatsApp, Telegram, email, morada, site, ideias de presente, notas**. Em **«Quem é para ti»**, se escolher **Outro**, pode escrever a palavra certa.
- **A foto**: toque em «Escolher a foto»; **faça pinça com dois dedos** para ampliar e **arraste** até o rosto ficar no oval. Mais tarde pode **🔄 Recentrar**.
- Cada pessoa tem a sua **ficha com moldura néon** da cor do seu **signo do zodíaco**, escolhido pela data. **Os signos mexem-se** (o Carneiro dá uma cabeçada com olhos de fogo, os Peixes nadam devagar, o Caranguejo anda de lado…).
- Por baixo da ficha há botões para **ligar, WhatsApp, Telegram, email, site**. A lista segue o **próximo aniversário** («🎉 Hoje!» se for hoje).
- Se **a pessoa já partiu**, marque **🕯️ Esta pessoa já não está connosco**: aparece uma **vela acesa**, a ficha passa para **Em memória** e encontra **⚰️ Onde repousa** (tipo de sepultura, cemitério, posição, concessão, lâmpada votiva, telefone e horário do cemitério, fotos da lápide), a **oração do eterno descanso**, **✍️ um pensamento** e **🎙️ uma mensagem de voz**.
- O **botão verde ⏻** dentro da ficha abre o **📖 Diário das memórias** (ver a sua ficha).
- ✏️ **Editar** muda os dados (o que não toca fica como estava); 🗑️ **Eliminar** manda a ficha para o Lixo.""",
                     "aniversários aniversário signo zodíaco ficha pessoa foto contactos whatsapp telegram falecido vela memória sepultura diário"),
    "x_diario": ("📖 O Diário das memórias (fotos, textos, música)", """Dentro da ficha de cada pessoa em **🎂 Aniversários**, em baixo à direita, está o **botão verde ⏻**. Toque: **a ficha desaparece e o diário abre**, com as fotos empilhadas como páginas de um livro.

- **Virar páginas**: **◀ Anterior** e **Seguinte ▶** em cima. O **botão vermelho ⏻**, entre os dois, fecha o diário e a ficha volta.
- **Passagem automática**: as fotos mudam sozinhas a cada **7 segundos**; em **⏱️ Passagem automática** escolha os segundos ou desligue. Cada foto **entra e sai com um efeito sempre diferente**.
- **Adicionar fotos**: **➕ Adicionar mais fotos** (as que quiser, sem limite). Para cada foto vê uma **pré-visualização**: **pinça** com dois dedos para ampliar e **arrastar** para mover; pode escrever **textos coloridos** (cor, letra, tamanho, posição) e pôr **ícones** (corações, flores, velas…). Depois **💾 Guardar a página**. As fotos ficam mais leves sozinhas sem perder qualidade.
- **Mudar depois**: com **✏️ Textos e ícones** tira ou muda textos e ícones quando quiser; **↩️ Anular a última alteração** repõe como estava (a foto original nunca é tocada). Em **🗂️ Gerir as páginas** move uma página **⬆️ ⬇️**, **🔄 muda a foto** ou **🗑️ elimina-a**.
- **Música**: em **🎵 Música do diário** escolha um ficheiro **MP3** (guarda-se sozinho). Começa ao tocar no botão verde; em baixo a **barra do volume** (tocar ou arrastar) e ▶/🔊 para pausar. Para mudar, escolha outro ficheiro.""",
                 "diário das memórias diário fotos páginas botão verde vermelho passagem música mp3 volume textos ícones efeitos gerir páginas aniversários"),
    "f_ia_documenti": ("🤖 Pôr a IA a reler e reclassificar os documentos", """Em **Saúde → Documentos de saúde** abra **🤖 Reclassificar os documentos com a IA**.

1. Vê **«Por verificar: X de Y»**: a IA lê **só os documentos ainda não verificados** (marque «Reler também os já verificados» para reler todos).
2. Toque em **🔍 Teste: ler e classificar**. Aparece um **quadro sempre aberto** que se atualiza sozinho: em que documento vai, há quantos segundos, a que serviço está a perguntar, quantos leu, quanto falta. Os pontos **●●●○** a mexer indicam que está a trabalhar.
3. **Pode usar outras apps ou desligar o ecrã**: a leitura continua sozinha. Cada documento é guardado logo que lido, nada se perde.
4. Um documento que fica bloqueado é **saltado após cerca de 2 minutos** («demasiado lento, saltado») e volta a tentar-se na próxima vez. **⏹ Parar a leitura** mantém os já lidos.
5. As **🟡 Propostas da IA para confirmar** aparecem no mesmo quadro, uma por documento: deixe marcado o que está certo e toque em **✅ Aplicar**; **✖ Não aplicar** deixa tudo como está. O que corrigiu à mão nunca é tocado.

Também **🔄 Reler os documentos já arquivados** (leitura sem IA) mostra **«Por reler: X de Y»** e não volta a propor os já feitos.""",
                       "reclassificar documentos ia inteligência artificial reler leitura em curso propostas aplicar verificados segundo plano outras apps parar"),
    "f_numeri_doc": ("🔢 O N.º dos documentos de saúde (para o médico)", """Cada documento de saúde tem um **número**: o **N.º 1 é o mais recente**, depois a descer até ao mais antigo. Vê-o num **quadrado verde** em cada ficha e na coluna **N°** do **resumo PDF** da Saúde.

**Para que serve:** dá o resumo ao médico; ele diz «traga-me o 4, o 12 e o 17». Escreva o número (por exemplo **12**) na caixa **🔍 Procurar** dos Documentos de saúde e aparece **só esse documento**.

**Atenção:** quando junta um documento novo, ele passa a ser o N.º 1 e os outros **descem um**. Se entretanto juntou documentos, **crie de novo o resumo PDF**. No PDF as datas já não ficam partidas em duas linhas.""",
                     "número documentos n.º médico resumo pdf procurar número ordem mais recente traga-me"),
    "f_gruppo": ("🩸 Grupo sanguíneo e certificado", """Na ficha da pessoa em **Saúde**: se falta o grupo sanguíneo, toque em **🩸 Inserir o grupo sanguíneo**, escolha-o e guarde. Pode mudá-lo quando quiser com **Editar**.

Por baixo pode **anexar o certificado do grupo sanguíneo** (PDF ou foto): escolha o ficheiro e guarda-se sozinho. Vê-o, descarrega-o ou tira-o quando quiser.""",
                 "grupo sanguíneo sangue certificado anexar pdf foto ficha pessoa"),
    "f_wiki": ("📖 «O que é?»: explicação simples da Wikipédia", """Em **Saúde → Documentos de saúde** e em **Saúde → Medicamentos** há o menu **📖 O que é? Explicação simples (Wikipédia)**.

Escreva o nome de um **exame, uma doença ou um medicamento** (por exemplo *ecodoppler*, *duloxetina*): se houver vários artigos escolha o certo e leia **duas linhas de explicação**, na língua da app, com o botão para abrir a página completa.

É **informação geral**, gratuita: **não é um conselho médico**. Para o seu caso pergunte sempre ao médico ou ao farmacêutico.""",
               "o que é explicação wikipédia exame doença medicamento significado palavra relatório"),
    "x_meteo": ("🌦️ Avisos meteorológicos úteis", """Avisos **só quando são precisos**, no topo das secções:
- **Saúde**: **calor forte** (beber muitas vezes, não sair das 11 às 17, atenção aos idosos e às crianças) e **frio intenso**;
- **Carro**: **geada** (gelo no para-brisas e nas estradas), **chuva forte**, **rajadas de vento**;
- **Animais**: **calor** (passeios cedo ou à noite, alcatrão que queima, água fresca, nunca no carro) e **frio**.

**Para os ligar:** **Utilidades → 🌦️ Avisos meteorológicos** → escreva a sua cidade → escolha a certa → **💾 Usar esta cidade**. Aí vê também as temperaturas dos próximos dias e pode **desligar** os avisos. Cada um escolhe a sua cidade.

As previsões são do **Open-Meteo**: gratuito, sem chaves nem registo, para uso não comercial.""",
                "tempo meteorologia avisos calor frio geada chuva vento cidade previsão open-meteo"),
    "x_voci_libere": ("✍️ Um nome à sua escolha nas listas com «Outro»", """Nas listas pendentes que têm a opção **Outro** (tipos de documento, divisões, espécies de animais, sepulturas, funções dos médicos, categorias do condomínio, formas de pagamento, «Quem é para ti», documentos INPS…):
1. escolha **Outro**;
2. aparece **✍️ Não está na lista? Escreva o nome que quiser**: escreva o nome exato (por exemplo **Ecocert**);
3. guarde como sempre: fica guardado **o seu nome**, não «Outro».

Nas fichas com o botão de confirmação em baixo a caixa está sempre lá, por baixo da lista, e só conta se escolheu «Outro». **O nome fica na lista**: da próxima vez já lá está, antes de «Outro».""",
                      "outro nome à escolha lista pendente escrever nome opção personalizada ecocert não está na lista"),
    "x_lingua": ("🌐 A língua da app", """**Entra-se na língua que se vê na página de acesso.** Se quiser outra língua, escolha-a no menu **🌐 Lingua / Language** antes de tocar em **Entrar**: fica guardada.

O telefone lembra-se da **última língua usada**: da próxima vez a página de acesso já abre nessa língua. Dentro da app a língua muda-se no menu **☰** em cima à esquerda.

Todas as páginas estão na língua escolhida: as frases novas traduzem-se sozinhas na primeira vez que uma página abre (cerca de um minuto) e depois ficam guardadas para todos. Também **o assistente** responde na língua escolhida.""",
                 "língua italiano inglês espanhol francês alemão romeno árabe português mudar língua acesso tradução"),
}, {
    "nv_diario": ("Diário das memórias", "Utilidades → 🎂 Aniversários → botão verde ⏻ na ficha: fotos, textos, ícones, música"),
    "nv_ia": ("Documentos lidos pela IA", "Saúde → Documentos de saúde → 🤖 Reclassificar: funciona mesmo se usar outras apps"),
    "nv_numeri": ("N.º dos documentos", "Saúde → Documentos de saúde: o N.º 1 é o mais recente; procure por número"),
    "nv_meteo": ("Avisos meteorológicos", "Utilidades → 🌦️ Avisos meteorológicos: escolha a sua cidade"),
    "nv_wiki": ("O que é?", "Saúde → Documentos de saúde e Medicamentos: explicação simples da Wikipédia"),
    "nv_altro": ("Nomes à escolha", "Nas listas com «Outro»: escreva o nome que quiser"),
})


ga_traduci('pt', {"l_festivita": ('📅 Feriados no Controlo de horas', 'Em **Trabalho → 🧮 Controlo de horas**, depois de carregar a folha de horas e o recibo de vencimento, há **📅 Feriados**.\n\nA app conhece sozinha os **feriados nacionais** (também a **Segunda-feira de Páscoa**, que muda todos os anos) e a **festa do padroeiro** da sua cidade, que escolhe uma vez em **⛪ Festa do padroeiro e feriados do ano** (para Turim: São João, 24 de junho) e depois toca em **💾 Lembrar o padroeiro**.\n- **Aviso vermelho**: trabalhou num feriado que na folha **não está marcado como feriado**. Vê os dias, as horas e uma estimativa do que pode perder (o feriado paga-se a 65%, as horas extra normais a 20%). Marque «feriado» na folha e volte a carregar, ou pergunte aos recursos humanos.\n- **Aviso amarelo**: um dia está marcado como feriado mas não é feriado nem domingo: verifique (pode valer uma regra do seu contrato).\n\nOs feriados vêm do **Nager.Date** (gratuito, sem chave); se não responder, a app calcula-os.', 'feriados feriado segunda-feira de páscoa padroeiro controlo de horas recibo horas extra')}, {})
