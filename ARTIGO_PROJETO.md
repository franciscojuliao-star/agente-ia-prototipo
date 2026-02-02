# AVA RAG: Sistema de Geração de Conteúdo Educacional com Inteligência Artificial

## Resumo

Este trabalho apresenta o desenvolvimento de um Ambiente Virtual de Aprendizagem (AVA) que utiliza Inteligência Artificial Generativa para automatizar a criação de materiais didáticos. O sistema emprega técnicas de RAG (Retrieval-Augmented Generation) combinadas com LLM (Large Language Model) local para gerar quizzes, resumos e flashcards a partir de materiais fornecidos por professores, mantendo total privacidade dos dados educacionais.

**Palavras-chave:** Inteligência Artificial, LLM, RAG, Educação, Geração de Conteúdo.

---

## 1. Introdução

A crescente demanda por conteúdo educacional personalizado e a sobrecarga de trabalho dos docentes motivaram o desenvolvimento de soluções baseadas em IA para o ambiente educacional. Este projeto propõe um sistema que auxilia professores na criação de materiais didáticos, utilizando seus próprios conteúdos como base para geração automatizada.

---

## 2. Objetivos

### 2.1 Objetivo Geral
Desenvolver uma plataforma educacional que utiliza IA generativa para automatizar a criação de conteúdo didático a partir de materiais fornecidos por professores.

### 2.2 Objetivos Específicos
- Implementar sistema de upload e processamento de materiais (PDF, vídeos, textos)
- Desenvolver pipeline RAG para contextualização da IA com material do professor
- Criar geração automatizada de quizzes, resumos e flashcards
- Garantir controle de qualidade através de aprovação docente
- Manter privacidade total dos dados com processamento local

---

## 3. Justificativa e Importância

| Problema | Solução Proposta |
|----------|------------------|
| Professores gastam horas criando avaliações | Geração automática em segundos |
| Conteúdo genérico não reflete a aula | IA usa material específico do professor |
| APIs de IA expõem dados sensíveis | Processamento 100% local |
| Ferramentas pagas são inacessíveis | Sistema gratuito e open-source |

O projeto democratiza o acesso à IA educacional, permitindo que instituições com recursos limitados utilizem tecnologia de ponta sem custos de API ou preocupações com privacidade.

---

## 4. Fundamentação Teórica

### 4.1 LLM (Large Language Model)
Modelos de linguagem treinados em bilhões de textos, capazes de compreender e gerar texto em linguagem natural. O projeto utiliza o Llama 3.2, modelo open-source da Meta.

### 4.2 RAG (Retrieval-Augmented Generation)
Técnica que combina busca de informação com geração de texto. Antes de gerar conteúdo, o sistema busca trechos relevantes do material do professor, fornecendo contexto específico para a IA.

### 4.3 Embeddings e Busca Vetorial
Representação numérica de textos que permite busca por similaridade semântica, não apenas palavras-chave.

---

## 5. Metodologia e Arquitetura

### 5.1 Stack Tecnológica

| Camada | Tecnologia | Função |
|--------|------------|--------|
| Frontend | React + Vite | Interface do usuário |
| Backend | FastAPI + Python | API REST |
| Banco de Dados | PostgreSQL | Dados estruturados |
| Banco Vetorial | ChromaDB | Busca semântica |
| LLM | Ollama + Llama 3.2 | Geração de conteúdo |
| Embeddings | Sentence Transformers | Vetorização de texto |

### 5.2 Fluxo do Sistema

```
Professor → Upload Material → Processamento → Armazenamento Vetorial
                                                      ↓
Aluno ← Conteúdo Aprovado ← Aprovação Professor ← Geração IA
```

---

## 6. Funcionalidades

### Para Professores
- Upload de materiais (PDF, YouTube, links, texto)
- Geração de quizzes com níveis de dificuldade
- Geração de resumos estruturados
- Geração de flashcards para revisão
- Aprovação/edição antes de publicar

### Para Alunos
- Acesso a conteúdos por disciplina
- Realização de quizzes com feedback imediato
- Estudo com flashcards interativos
- Busca semântica nos materiais
- Histórico de desempenho

---

## 7. Resultados e Impacto

### 7.1 Impacto Educacional
- **Redução de tempo:** Criação de quiz de 2h → 30 segundos
- **Personalização:** Conteúdo alinhado com material da disciplina
- **Escalabilidade:** Atende múltiplas turmas simultaneamente
- **Acessibilidade:** Gratuito e executável em hardware comum

### 7.2 Impacto Tecnológico
- Demonstra viabilidade de IA local em ambiente educacional
- Arquitetura replicável para outras instituições
- Código aberto para contribuições da comunidade

### 7.3 Impacto Social
- Democratização do acesso à IA educacional
- Privacidade de dados de alunos e professores
- Independência de grandes empresas de tecnologia

---

## 8. Limitações e Trabalhos Futuros

### Limitações Atuais
- Modelo local inferior em qualidade a GPT-4
- Requer hardware com GPU para melhor performance
- Possibilidade de alucinações da IA (mitigada por aprovação docente)

### Trabalhos Futuros
- Integração com sistemas acadêmicos (SIGAA)
- Geração de provas completas
- Análise de desempenho com dashboards
- Suporte a múltiplos idiomas
- Deploy em nuvem com auto-scaling

---

## 9. Conclusão

O projeto AVA RAG demonstra a viabilidade de utilizar Inteligência Artificial Generativa no contexto educacional brasileiro, mantendo privacidade e custo zero. A combinação de LLM local com técnicas de RAG permite gerar conteúdo contextualizado e relevante, reduzindo significativamente o tempo de preparação de materiais didáticos. O sistema representa um passo importante na democratização da IA para educação.

---

## Referências

- VASWANI, A. et al. Attention Is All You Need. *NeurIPS*, 2017.
- LEWIS, P. et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS*, 2020.
- META AI. Llama 3: Open Foundation Language Models. 2024.
- REIMERS, N.; GUREVYCH, I. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP*, 2019.

---

## Informações do Projeto

| Item | Descrição |
|------|-----------|
| **Disciplina** | Projeto Integrador |
| **Tecnologias** | Python, FastAPI, React, PostgreSQL, Ollama, ChromaDB |
| **Licença** | MIT (Open Source) |
