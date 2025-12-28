# 📄 RenderCV Visual Builder

Uma interface visual poderosa e intuitiva para criar currículos profissionais utilizando o motor de renderização [RenderCV](https://github.com/sinaatalay/rendercv).

Este projeto transforma a experiência de editar arquivos YAML complexos em uma jornada visual guiada, permitindo que qualquer pessoa crie currículos de alto nível com design impecável em minutos.

---

## ✨ Funcionalidades Principais

### 🎨 Dois Modos de Criação

- **Modo Template (Guiado):** Escolha entre designs consagrados (Classic, ModernCV, SB2Nov) e preencha apenas as seções recomendadas. Ideal para quem quer rapidez e estrutura.
- **Modo Builder (Do Zero):** Liberdade total para adicionar seções de qualquer tipo, ordenar entradas e customizar cada detalhe do currículo.

### 🛠️ Editor Dinâmico

- **Formulários Inteligentes:** Campos que se adaptam ao tipo de entrada (Educação, Experiência, Projetos, Publicações, etc).
- **Campos Customizados (Arbitrary Keys):** Adicione qualquer campo extra que o seu template Typst suporte diretamente pela interface.
- **Validação em Tempo Real:** O sistema verifica campos obrigatórios e formatos de data antes de tentar renderizar, evitando erros comuns.

### 🚀 Renderização de PDF Local

- Integração direta com o RenderCV CLI.
- Renderização limpa e rápida utilizando Typst.
- **Download Instantâneo:** Baixe tanto o arquivo PDF final quanto o YAML gerado para uso futuro.

### 👓 Visualização em Tempo Real

- Painel lateral para inspecionar o código YAML gerado conforme você digita.
- Ideal para usuários avançados que querem entender ou copiar a estrutura de dados.

---

## 🚀 Como Começar

### Pré-requisitos

- Python 3.10 ou superior
- Pip (gerenciador de pacotes)

### 1. Instalação do RenderCV

O motor de renderização deve estar instalado no seu ambiente:

```bash
pip install rendercv
```

### 2. Configuração do Projeto

Clone o repositório e instale as dependências do frontend:

```bash
cd frontend
pip install -r requirements.txt
```

### 3. Execução

Inicie a aplicação com Streamlit:

```bash
streamlit run app.py
```

Acesse no navegador: `http://localhost:8501`

---

## 🏗️ Estrutura do Projeto

```text
cv_builder/
├── frontend/
│   ├── app.py             # Aplicação Streamlit principal (UI/UX)
│   ├── models.py          # Definições de dados com Pydantic e Schemas
│   ├── yaml_serializer.py # Lógica de conversão JSON -> YAML Clean
│   ├── api_client.py      # Integração com o RenderCV CLI (subprocess)
│   └── requirements.txt   # Dependências do projeto
├── README.md              # Documentação
└── .gitignore
```

---

## 🛠️ Tecnologias Utilizadas

- **[Streamlit](https://streamlit.io/):** Framework para criação da interface web interativa.
- **[RenderCV](https://github.com/sinaatalay/rendercv):** Motor de backend para geração de currículos baseados em YAML/Typst.
- **[Pydantic](https://docs.pydantic.dev/):** Validação de dados e modelagem de tipos.
- **[ruamel.yaml](https://yaml.readthedocs.io/):** Manipulação avançada de YAML preservando formatação e estilos de bloco.

---

## 📝 Regras de Negócio e Validação

- **Datas:** Suporta formatos `YYYY`, `YYYY-MM`, `YYYY-MM-DD` e a palavra chave `present`.
- **Seções:** Cada seção é tipada (EducationEntry, ExperienceEntry, etc). Uma vez definido o tipo do primeiro item, a seção mantém a consistência.
- **Design:** Suporte a temas personalizados e cores de destaque.

---

## 🤝 Contribuição

Sinta-se à vontade para abrir issues ou enviar pull requests. Toda contribuição que melhore a experiência visual ou adicione novos templates é bem-vinda!

---

## ⚖️ Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

_Desenvolvido com ❤️ por Antigravity para transformar a busca por emprego em uma experiência elegante._
