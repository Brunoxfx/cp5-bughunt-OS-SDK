# Entrega — Checkpoint 5 PetFiap

Grupo OS-SDK, turma 2CCPG. Integrantes e RMs estão no README.

## Revisão dos requisitos do PDF

| Requisito | Situação |
|---|---|
| Corrigir o projeto recebido com mudanças mínimas | Concluído; estrutura, endpoints e dependências mantidos. |
| 12 bugs corrigidos | Concluído; 12 commits `fix: bugNN`. |
| 6 ajustes de Clean Code | Concluído; 6 commits `refactor: cleanNN`. |
| 6 regras antes sem cobertura | Concluído; 6 testes novos em 6 commits `test: testeNN`, quatro inicialmente vermelhos e dois verdes. |
| 20 testes recebidos intactos e verdes | Validado por comparação byte a byte com o ZIP e execução da suíte. |
| Suíte completa verde | Validado: 26 testes, zero falhas, erros ou testes ignorados. |
| Primeiro commit original | Validado: todos os 25 arquivos originais correspondem ao ZIP recebido. |
| Configuração sem credenciais reais | Validado: `application.properties` mantém `SEU_RM/SUA_SENHA` e é idêntico ao original. |
| Nenhuma biblioteca nova | Validado: `pom.xml` idêntico ao original. |
| README completo | Concluído: identificação, 12 achados, 6 ajustes, 6 testes e 6 reflexões de 7 linhas cada. |
| API em execução, opcional | Validado com H2: 76 verificações de HTTP, regras e persistência. Oracle e Eclipse não executados nesta validação. |
| Conferência das reflexões pelos integrantes | Pendente. |
| Repositório público no GitHub | Publicado em [Brunoxfx/CP5-POO](https://github.com/Brunoxfx/CP5-POO), com o histórico completo. |
| Link no Teams, igual para todo o grupo | Pendente de envio. |

## Conteúdo do ZIP

O ZIP contém o projeto Maven, o README, o template recebido, os scripts de verificação, as evidências e `historico.bundle`, que preserva todos os commits. Não inclui arquivos temporários, credenciais reais nem o diretório de build `target`.

Para abrir no Eclipse, extraia o ZIP e importe a pasta com `pom.xml` como projeto Maven. Use JDK 17 ou superior.

Para restaurar o repositório com o histórico, execute na pasta extraída:

```powershell
git clone historico.bundle ../cp5-bughunt-OS-SDK-com-historico
cd ../cp5-bughunt-OS-SDK-com-historico
git log --oneline --reverse
mvn verify
```

Ao publicar, use esse repositório restaurado ou o repositório de trabalho original. Criar um repositório novo somente com os arquivos extraídos perderia os commits exigidos pelo PDF.

Entregue [https://github.com/Brunoxfx/CP5-POO](https://github.com/Brunoxfx/CP5-POO) no Teams, usando o mesmo link para todos os integrantes. O ZIP local não substitui essa etapa.
