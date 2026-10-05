# Checkpoint 5 — Bug Hunt PetFiap

API de agendamentos de banho, tosa e consulta veterinária corrigida a partir do projeto recebido. Foram mantidos Spring Boot, JPA, os endpoints, as dependências e os 20 testes originais.

## Identificação

**Grupo:** OS-SDK.

| Integrante | RM | Turma |
|---|---|---|
| Bruno Anselmo da Silva | 566521 | 2CCPG |
| Fernando de Almeida Godoi | 564820 | 2CCPG |
| Gabriel Ber Soares | 563520 | 2CCPG |
| Guilherme de Freitas Salgado | 562494 | 2CCPG |
| Vinicius Ribeiro Dias | 566468 | 2CCPG |

| Campo | Resultado |
|---|---|
| **Total de bugs corrigidos** | **12 / 12** |
| **Total de ajustes de Clean Code** | **6 / 6** |
| **Total de testes novos escritos** | **6 / 6** |
| **Suíte final** | **26 testes, 0 falhas, 0 erros, 0 ignorados** |

Repositório: [Brunoxfx/CP5-POO](https://github.com/Brunoxfx/CP5-POO).

Para executar os testes, use JDK 17 ou superior e `mvn verify`. A API também foi validada com Oracle FIAP, incluindo gravação, leitura e persistência após reinício. As credenciais locais não foram versionadas.

## Parte 1 — Bugs encontrados

As linhas abaixo se referem ao estado original do ZIP. Os caminhos partem de `src/main/java/br/com/fiap/petfiap/`. Cada correção tem seu próprio commit `fix: bugNN`.

| # | Sintoma observado (o que fiz/vi) | Causa raiz (arquivo e linha aproximada) | Correção aplicada | Conceito da disciplina |
|---|---|---|---|---|
| bug01 | O Builder recebeu `Rex`, mas `getPetNome()` retornou `null`. | `builder/AtendimentoBuilder.java:24`: `petNome = petNome` atribuía o parâmetro a ele mesmo. | Usado `this.petNome = petNome`. O teste original passou a preservar o nome. | Atributos, parâmetros e `this`, Aulas 1 e 4. |
| bug02 | O Builder construía um objeto sem nome ou sem porte, sem lançar a exceção esperada. | `builder/AtendimentoBuilder.java:41`: `construir()` delegava à Factory sem validar os campos obrigatórios. | Validado nome e porte nulos ou em branco antes da criação, com `IllegalArgumentException`. | Encapsulamento, nascimento válido e exceções, Aulas 3, 4 e 11. |
| bug03 | A Factory devolveu `Banho` quando o tipo solicitado era `TOSA`. | `factory/AtendimentoFactory.java:17`: o ramo `TOSA` instanciava a classe errada. | Instanciada `Tosa` no ramo correspondente. | Factory, abstração e polimorfismo, Aulas 7, 8 e 14. |
| bug04 | A consulta criada pela Factory perdeu nome, porte e tutor. Também nascia sem protocolo, horário e status inicial. | `model/ConsultaVeterinaria.java:17`: o construtor chamava `super()` vazio. | Repassados os cinco parâmetros ao construtor completo de `Atendimento`. | Herança e encadeamento de construtores, Aulas 4 e 6. |
| bug05 | Duas chamadas a `getInstancia()` devolveram objetos diferentes; os protocolos repetiram `1`. | `model/GeradorProtocolo.java:17–20`: a instância criada não era guardada no campo estático. | Guardada a instância e sincronizados o acesso e o incremento, preservando uma sequência global na execução. | Singleton e estado compartilhado, Aula 14. |
| bug06 | Outro objeto com o mesmo pet e horário passou pelo filtro de conflito. O mock retornou `null` ao salvar e o teste recebeu `NullPointerException`. | `service/AgendaService.java:23`: `==` comparava referências de `String` e `LocalDateTime`. | Usado `.equals()` nos dois valores. O conflito lança `HorarioOcupadoException` antes de salvar. | Igualdade de objetos, regras de negócio e mocks, Aulas 7, 11 e 15. |
| bug07 | A busca de ID inexistente retornou `null`, embora o teste exigisse uma exceção. | `service/AgendaService.java:36–43`: `catch (Exception)` capturava a exceção do `orElseThrow`. | Removida a captura genérica; `AtendimentoNaoEncontradoException` chega ao chamador. | Propagação de exceções unchecked, Aula 11. |
| bug08 | O teste novo de preços encontrou R$ 100 para banho pequeno, em vez de R$ 60; a revisão também mostrou os R$ 60 do grande. | `model/Banho.java:26–32`: preços dos portes pequeno e grande invertidos. | Corrigida a tabela para R$ 60, R$ 80 e R$ 100. | Regras nas subclasses e testes de regressão, Aulas 7 e 15. |
| bug09 | Uma referência `Atendimento` contendo uma `Tosa` retornou 30 minutos, em vez de 60. | `model/Tosa.java:40`: `getDuracaoMinutos(String porte)` não sobrescrevia o método sem parâmetros. | Corrigida a assinatura e adicionada a anotação `@Override`. | Sobrescrita versus sobrecarga, Aula 7. |
| bug10 | Agendar no passado acessou o repository e não lançou a exceção de validação esperada. | `service/AgendaService.java:20–21`: não verificava a data antes da consulta. | Recusado horário passado antes de qualquer acesso ao repository. Horário nulo também é recusado nesse caminho. | Validação antecipada, exceções e `verifyNoInteractions`, Aulas 11 e 15. |
| bug11 | `cancelar()` aceitou atendimento concluído; a revisão mostrou que aceitava também cancelado. | `model/Atendimento.java:63–65`: atribuía `CANCELADO` sem validar o estado atual. | Permitido cancelar somente `AGENDADO`; estados finais lançam `StatusInvalidoException` e permanecem intactos, sem salvar. | Estado do objeto, encapsulamento e exceções, Aulas 2, 3 e 11. |
| bug12 | A API iniciou com H2, mas o primeiro cadastro respondeu HTTP 500 por falta de ID. Os 26 testes unitários continuavam verdes. | `model/Atendimento.java:14–15`: havia `@Id`, sem estratégia de geração. | Adicionado `@GeneratedValue(strategy = GenerationType.IDENTITY)`. Cadastro e leitura pela API confirmam IDs gerados. | Identidade da entidade e persistência JPA, Aula 13. |

O bug12 foi encontrado na revisão do mapeamento e reproduzido pela API. Um repository mockado não executa o Hibernate, portanto a suíte unitária não detectava essa falha.

## Parte 2 — Ajustes de Clean Code

| # | Onde estava | Qual princípio/boas práticas era violado | O que eu mudei |
|---|---|---|---|
| clean01 | `factory/AtendimentoFactory.java`, parâmetros `p`, `t`, `n`, `po`, `tu`, `d` | Nomes não expressavam a finalidade dos dados. | Renomeados para `protocolo`, `tipo`, `petNome`, `petPorte`, `tutorNome` e `dataHora`. |
| clean02 | `service/AgendaService.java`, variáveis `novo`, `doPet` e `a` | Nomes curtos dificultavam acompanhar a regra de conflito. | Usados `novoAtendimento`, `atendimentosDoPet` e `atendimentoExistente`. |
| clean03 | `Atendimento`, `Banho`, `Tosa` e `ConsultaVeterinaria` | Valores de preço, pontos e duração apareciam como números sem nome. | Criadas constantes privadas para essas regras, preservando os valores do contrato. |
| clean04 | Recibo em `AgendaService` e impressão de criação em `GeradorProtocolo` | Regras de negócio misturadas com saída de console. | Extraída `apresentacao/ReciboAgendamento`; o controller imprime após agendar. Removida a impressão do construtor do Singleton. |
| clean05 | Final de `controller/AtendimentoController.java` | Método de desconto nunca usado e planejamento abandonado dentro do código. | Removidos `calcularDescontoFidelidade` e os comentários da funcionalidade futura. |
| clean06 | Builder, model e service | Comentário do Builder atribuía a validação ao controller; outros apenas repetiam nomes de métodos. | Removidos o comentário incorreto e comentários redundantes. Mantidas explicações úteis dos padrões e regras. |

Cada ajuste tem um commit `refactor: cleanNN`. A suíte inteira foi executada após cada ajuste.

## Parte 3 — Testes novos (regras que estavam sem cobertura)

Os seis testes estão em arquivos novos; nenhum arquivo da suíte entregue foi alterado. Seguem o padrão Arrange, Act e Assert. Dependências do service são substituídas por mocks.

| # | Teste escrito (classe.método) | Regra coberta | Resultado ao escrever (vermelho/verde) |
|---|---|---|---|
| teste01 | `BanhoPrecoTest.deveCobrarPrecoDaTabelaQuandoPorteVariar` | Preços de banho para pequeno, médio e grande. | Vermelho: revelou bug08. |
| teste02 | `TosaDuracaoTest.deveDurar60MinutosQuandoAtendimentoForTosa` | Tosa dura 60 minutos na chamada polimórfica sem parâmetros. | Vermelho: revelou bug09. |
| teste03 | `AgendaPassadoTest.deveRecusarAgendamentoSemConsultarBancoQuandoDataEstiverNoPassado` | Data passada lança `IllegalArgumentException` sem consultar nem salvar no repository. | Vermelho: revelou bug10. |
| teste04 | `AgendaCancelamentoInvalidoTest.deveRecusarCancelamentoQuandoAtendimentoNaoEstiverAgendado` | Concluído e cancelado recusam cancelamento, preservando o estado e sem salvar. | Vermelho: revelou bug11. |
| teste05 | `ConsultaPrecoTest.deveCobrar150ReaisQuandoPorteDaConsultaVariar` | Consulta custa R$ 150 nos três portes. | Verde de cara: cálculo já correto. |
| teste06 | `AgendaCancelamentoTest.deveSalvarCancelamentoQuandoAtendimentoEstiverAgendado` | Cancelar agendado muda para `CANCELADO` e salva o mesmo objeto. | Verde de cara: esse caminho já correto. |

Cada teste tem um commit `test: testeNN`, separado do commit que corrige a causa.

## Parte 4 — Perguntas de reflexão

### 1. A suíte como contrato (Aula 15)

A primeira execução confirmou 20 testes e 9 falhas, como no enunciado.<br>
Em `AtendimentoBuilderTest`, `expected: <Rex> but was: <null>` mostrou que o nome se perdia na montagem.<br>
Ao ler `comPet`, encontramos `petNome = petNome` e corrigimos o atributo com `this`.<br>
Na Factory, a mensagem esperava `Tosa`, mas recebeu `Banho`, apontando diretamente ao ramo errado.<br>
No conflito de horário, o teste esperava `HorarioOcupadoException`, mas recebeu `NullPointerException` depois de passar pelo filtro.<br>
Corrigimos as causas no código de produção e rodamos a suíte após cada mudança, preservando os testes.<br>
Comparado com curl manual, o teste repete as mesmas verificações rapidamente e acusa regressões; curl continua útil para conferir HTTP e persistência.

### 2. Mock e injeção de dependência (Aulas 13 a 15)

Em produção, o Spring cria o bean `AgendaService` e injeta o repository no campo com `@Autowired`.<br>
O Spring Data fornece uma implementação de `AtendimentoRepository` ligada à persistência JPA.<br>
Em `AgendaServiceTest`, quem inicializa os objetos de teste é a extensão `MockitoExtension`.<br>
O `@Mock` cria um repository falso e o `@InjectMocks` coloca esse falso no service.<br>
`when(repository.findById(1L)).thenReturn(...)` define apenas a resposta daquele cenário, sem executar SQL.<br>
Não usamos `@SpringBootTest`, então não iniciamos o container nem conectamos ao Oracle.<br>
No teste de data passada, `verifyNoInteractions(repository)` comprova que a validação termina antes de qualquer consulta ou gravação.

### 3. `==` vs `.equals()` (Aula 7)

O filtro de `AgendaService.agendar` comparava nome e data com `==`, que verifica referências de objetos.<br>
Duas requisições podem conter o mesmo texto e horário, mas gerar objetos diferentes na memória.<br>
Os literais `"Rex"` podem compartilhar uma referência pelo pool de Strings, fazendo o primeiro trecho funcionar por sorte.<br>
Isso não garante igualdade para textos montados na execução nem para instâncias de `LocalDateTime`.<br>
O teste original cria outro horário com `LocalDateTime.parse`, preservando o valor e trocando o objeto.<br>
A correção usa `.equals()` nos dois campos e mantém a exigência de status `AGENDADO`.<br>
Assim, o conflito é recusado pelo valor dos dados, e `verify(repository, never()).save(any())` confirma que nada é salvo.

### 4. Sobrescrita vs sobrecarga (Aula 7)

`Atendimento` oferece `getDuracaoMinutos()` sem parâmetros e retorna a duração padrão de 30 minutos.<br>
A classe `Tosa` tinha `getDuracaoMinutos(String porte)`, criando outra assinatura.<br>
Isso é sobrecarga: o nome coincide, mas os parâmetros diferem, por isso o código compilava.<br>
O resumo do controller chama o método sem argumentos por uma referência `Atendimento` e recebia os 30 minutos herdados.<br>
Corrigimos `Tosa` para declarar `getDuracaoMinutos()` sem parâmetros, retornando 60.<br>
A anotação `@Override` confirma a sobrescrita e teria provocado erro de compilação na assinatura antiga.<br>
`TosaDuracaoTest` reproduz a chamada pelo tipo abstrato, protegendo o comportamento polimórfico usado pela API.

### 5. Singleton manual vs bean do Spring (Aula 14)

`GeradorProtocolo` guarda uma única instância estática para compartilhar o contador entre chamadas.<br>
A versão original criava um objeto quando o campo estava nulo, mas não guardava esse objeto em `instancia`.<br>
Por isso, cada chamada podia começar outro contador e devolver novamente o protocolo 1.<br>
A correção atribui o objeto ao campo estático e sincroniza a obtenção da instância e o incremento.<br>
Os testes confirmam a mesma referência e os protocolos 1, 2 e 3; a sequência é da execução e reinicia ao encerrar a JVM.<br>
`AgendaService` é um bean `@Service`, cujo escopo padrão é singleton dentro do contexto do Spring.<br>
Nesse caso, o container administra a criação e reutilização; isso não significa que qualquer estado mutável do service seja automaticamente seguro para concorrência.

### 6. Cobertura de testes: onde parar? (Aula 15)

Os testes novos de preço fixo da consulta e cancelamento válido passaram sem correção adicional.<br>
Vale mantê-los porque documentam regras que estavam sem proteção e detectam futuras regressões.<br>
Os outros quatro revelaram preço invertido, duração herdada, data passada aceita e cancelamento inválido.<br>
Com prazo curto, eu priorizaria regras com maior impacto e combinações de caminho feliz e recusa.<br>
Neste projeto, isso inclui não salvar em conflito, impedir mudanças em estados finais e preservar os valores da tabela.<br>
Uma porcentagem de cobertura não substitui boas asserções: executar um método sem verificar o resultado pode deixar o bug passar.<br>
O bug12 mostrou outro limite: mocks não validam o mapeamento JPA, então acrescentamos uma verificação da API com H2.
