<img width="1016" height="372" alt="main(1)" src="https://github.com/user-attachments/assets/d2451456-959a-4b50-b621-c7464ac77be6" />

<h1 align='center'>
Organizei
</h1>
<div align='center'>
Aplicação web de gestão financeira pessoal: controle de gastos, investimentos, metas e assinaturas.
<br><br>
    
**Disciplina:** Fundamentos de Desenvolvimento de Software — Turma 2B — 2026.1 \
**Link do deploy:**  https://organizei.lat \
**Repositório:** [github.com/DoctahW/organizei](https://github.com/DoctahW/organizei)
</div>

---

<details>
<summary><h2>Entrega 01 ✅ — 09/03/2026</h2></summary>

### Histórias de Usuário

Documento com as 9 histórias de usuário e critérios de aceitação em BDD (Dado / Quando / Então):
[Acessar documento](https://docs.google.com/document/d/1egnmUUYxPPLPzJMuwT_RmfhdqImwkjjIUY5sBWSnhy4/edit?usp=sharing)

### JIRA — Sprint e Backlog

![Backlog JIRA](https://i.imgur.com/lBkPJIF.png)
![Quadro JIRA](https://i.imgur.com/XrWvbjp.png)

### Protótipos Lo-Fi

Protótipos de baixa fidelidade no Figma cobrindo 5 histórias:
[Acessar no Figma](https://www.figma.com/design/j0wEhFfWl55RNM137RW6rR/ORGANIZEI_Lo-Fi?node-id=0-1&t=34MYVU5atat7Rbxn-1)

### Screencast — Protótipo Lo-Fi

Apresentação do protótipo com áudio e legenda:
[Assistir no YouTube](https://youtu.be/tkBOIxoyT6g)

</details>

---

<details>
<summary><h2>Entrega 02 ✅ — 30/03/2026</h2></summary>

### Histórias Implementadas (Sprint 1)

Foram selecionadas 3 histórias para implementação nesta entrega:

1. Registrar entradas e saídas financeiras
2. Impor limites de gastos
3. Estabelecer objetivos/metas de consumo

### JIRA — Sprint 01

[Acessar Sprint 01 no JIRA](https://organizei.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog)

### Issue/Bug Tracker (GitHub)

Os problemas e sugestões foram classificados de acordo com categorias (bug, enhancement, etc) e milestones por sprint.

#### Issues

![Print da aba Issues](docs/imgs/print_issues.png)

#### Milestones

![Print da aba Milestones na Sprint 1](docs/imgs/print_milestone_sprint1.png)

### Deploy

**Link de acesso:** https://organizei.lat

#### Como acessar

Para fins de teste, utilize as credenciais abaixo (sistema de registro ainda não implementado):

| Campo   | Valor   |
| ------- | ------- |
| Usuário | `admin` |
| Senha   | `1234`  |

#### Screencast — Sistema em produção

[Assistir no YouTube](https://youtu.be/PJ50jg6RfzQ)

### Programação em Par

Dividimos o grupo em três duplas, com cada dupla responsável por uma história. Cada integrante da dupla escolheu uma área de atuação (Front-end ou Back-end), mas todos se ajudaram na revisão das funcionalidades implementadas.

1. **Registrar entradas e saídas financeiras — Larissa e Gabriel**

   O desenvolvimento foi iniciado com a criação do modelo referente ao formulário de inserção de uma nova transação. A implementação ocorreu de forma colaborativa e alternada, à medida que cada etapa do código era concluída.

   Inicialmente, Larissa ficou responsável pela construção do formulário em HTML e pela implementação das rotas do tipo POST. Em seguida, Gabriel deu continuidade ao trabalho, finalizando a rota do tipo GET e realizando as demais integrações necessárias com o banco de dados.

   Posteriormente, os demais integrantes conduziram a revisão das alterações, promovendo ajustes relacionados à integração com outras partes do sistema, incluindo interfaces e rotas do projeto.

2. **Impor limites de gastos — Vinícius e Heitor**

   O desenvolvimento foi iniciado com a implementação de um app budget para a definição de limites de gastos, com data específica e tracking em tempo real do fluxo monetário das contas registradas. A implementação ocorreu de forma colaborativa e alternada, consistindo na intercalação de funções e participação efetiva da dupla na construção do código.

   Com a implementação do app e a definição de funcionalidades sendo feito por Heitor, houve a colaboração da dupla para o estabelecimento de um sistema efetivo, funcional e agradável, contando com implementações de requerimento de login, rota de URL e aprimoramento do front-end por Vinicius.

   Por fim, os demais integrantes conduziram a revisão das alterações, promovendo ajustes de integração com outras partes do sistema.

3. **Estabelecer objetivos/metas de consumo — Ariel e Euclides**

   O desenvolvimento foi iniciado com base no modelo do formulário de estabelecer objetivo/meta de consumo. A implementação ocorreu de forma colaborativa e alternada: em cada entrega, um integrante ficou responsável pelo backend enquanto o outro cuidava do frontend.

   Euclides ficou encarregado da construção do app goals no Django, desenvolvendo os códigos do backend e integrando-os ao HTML. Em seguida, Ariel deu continuidade ao trabalho refinando a interface visual com CSS e reorganizando a estrutura do HTML.

   Por fim, os demais integrantes conduziram a revisão das alterações, promovendo ajustes de integração com outras partes do sistema.

### Quadro da Sprint 02

#### Quadro Sprint 2 + Backlog Atualizado

<img width="1986" height="946" alt="image" src="https://github.com/user-attachments/assets/d732909f-4623-4b19-8c7b-e2c896124302" />

#### Board da Sprint 2

<img width="1975" height="345" alt="image" src="https://github.com/user-attachments/assets/bd3824a6-452b-4d01-9dd5-a65566b2cc71" />

</details>

---

<details>
<summary><h2>Entrega 03 ✅ — 27/04/2026</h2></summary>

### Histórias Implementadas (Sprint 2)

Foram selecionadas 4 histórias para implementação nesta entrega:

1. Cadastrar e gerenciar contas bancárias
2. Visualizar saldo das contas bancárias
3. Visualizar painel financeiro (dashboard)
4. Categorizar transações

### JIRA - Sprint 02
<img width="2289" height="873" alt="screenshot-2026-04-27_19-34-33" src="https://github.com/user-attachments/assets/f2d95c3d-2692-4303-be29-7c0f5edf97ca" />

### Screencast com as histórias implementadas

[Link para o vídeo screencast](https://youtu.be/yD7eFAaO51A)

#### Screencast testando as histórias implementadas via testes E2E:

[Link](https://youtu.be/DgT2rhwJekw)

### Programação em par (atualização)

Nosso grupo seguiu o mesmo procedimento da entrega anterior, com três duplas e cada uma com uma história para implementar, exceto uma dupla que ficou com duas histórias. Porém, independente desta divisão, os componentes do grupo como um todo ajudaram-se uns aos outros.

### Issues/Bug tracker (GitHub)

#### Milestone da Sprint 2:

<img width="1161" height="414" alt="image" src="https://github.com/user-attachments/assets/bdeae1e8-8b7e-4986-a712-70b63aa9ad2b" />

#### Issues resolvidas:

Estão incluidas funcionalidades em falta e bugs que foram encontrados ao longo do uso da aplicação.

<img width="1204" height="517" alt="image" src="https://github.com/user-attachments/assets/b574b329-7b84-4f60-8145-8758fda262b1" />

#### Issues em aberto:

Algumas dessas issues inclui a melhora de alguma funcionalidade do sistema e alguns bugs não resolvidos.

<img width="1198" height="385" alt="image" src="https://github.com/user-attachments/assets/c621cb67-5671-4166-9c75-aa9830e023db" />


#### Quadro da Sprint 3 + Backlog atualizado
<img width="2290" height="1335" alt="screenshot-2026-04-27_19-39-06" src="https://github.com/user-attachments/assets/4ece9428-2d11-4e7f-9ec8-eba6cfd630ff" />

#### Board da Sprint 3
<img width="2286" height="561" alt="screenshot-2026-04-27_19-50-32" src="https://github.com/user-attachments/assets/cf5d14cc-6cf1-47ef-8646-5726f38aadf4" />

</details>


---

## Equipe

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/ariel-cs"><img src="https://avatars.githubusercontent.com/u/235714404?v=4?s=100" width="100px;" alt="Ariel"/><br /><sub><b>Ariel</b></sub></a><br /><a href="https://github.com/DoctahW/organizei/commits?author=ariel-cs" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Torzinus"><img src="https://avatars.githubusercontent.com/u/240728979?v=4?s=100" width="100px;" alt="Heitor de Carvalho"/><br /><sub><b>Heitor de Carvalho</b></sub></a><br /><a href="https://github.com/DoctahW/organizei/commits?author=Torzinus" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/venici-o"><img src="https://avatars.githubusercontent.com/u/234500103?v=4?s=100" width="100px;" alt="Vinicius"/><br /><sub><b>Vinicius</b></sub></a><br /><a href="https://github.com/DoctahW/organizei/commits?author=venici-o" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://larissagiovanna.github.io/LarissaGiovanna/"><img src="https://avatars.githubusercontent.com/u/143462771?v=4?s=100" width="100px;" alt="Larissa Giovanna"/><br /><sub><b>Larissa Giovanna</b></sub></a><br /><a href="https://github.com/DoctahW/organizei/commits?author=LarissaGiovanna" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/RiosGabri"><img src="https://avatars.githubusercontent.com/u/222075163?v=4?s=100" width="100px;" alt="Gabriel Parméra"/><br /><sub><b>Gabriel Parméra</b></sub></a><br /><a href="https://github.com/DoctahW/organizei/commits?author=RiosGabri" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/DoctahW"><img src="https://avatars.githubusercontent.com/u/100718374?v=4?s=100" width="100px;" alt="João Euclides"/><br /><sub><b>João Euclides</b></sub></a><br /><a href="https://github.com/DoctahW/organizei/commits?author=DoctahW" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
