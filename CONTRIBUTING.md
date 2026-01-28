# Contribuindo com o Portal Cautivo Municipal

Agradecemos pelo interesse em contribuir com o Portal Cautivo Municipal! Este documento contém informações importantes para contribuidores.

## Como Contribuir

### 1. Fork do Projeto
- Clique em "Fork" no canto superior direito do repositório
- Clone o fork para sua máquina local

```bash
git clone https://github.com/seu-usuario/portal-cautivo-municipal.git
cd portal-cautivo-municipal
```

### 2. Configuração do Ambiente

#### Requisitos
- Python 3.8+
- pip

#### Instalação de Dependências
```bash
pip install -r requirements.txt
```

#### Configuração de Variáveis de Ambiente
```bash
cp .env .env.local
# Edite .env.local com suas configurações
```

### 3. Diretrizes de Código

#### Estilo de Código
- Siga o padrão PEP 8
- Use docstrings para funções e classes
- Comentários em português para lógica complexa

#### Nomenclatura
- **Variáveis**: `snake_case`
- **Funções**: `snake_case`
- **Classes**: `PascalCase`
- **Constantes**: `UPPER_SNAKE_CASE`

#### Exemplos de Código

```python
def validar_email(email: str) -> bool:
    """
    Valida o formato de um endereço de email.
    
    Args:
        email (str): Endereço de email a ser validado
        
    Returns:
        bool: True se o email for válido, False caso contrário
    """
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None
```

### 4. Testes

#### Testes Unitários
- Crie testes para novas funcionalidades
- Use o módulo `unittest` do Python
- Nomeie os arquivos de teste como `test_*.py`

#### Execução de Testes
```bash
python -m unittest discover tests/
```

### 5. Processo de Pull Request

#### Antes de Enviar
1. **Teste localmente** - Certifique-se de que tudo funciona
2. **Verifique lint** - Use ferramentas de lint se disponíveis
3. **Atualize documentação** - Atualize README.md se necessário
4. **Commit significativo** - Use mensagens de commit descritivas

#### Mensagens de Commit
Use o formato:
```
Tipo: Descrição curta da mudança

Descrição detalhada da mudança (se necessário)
- Ponto 1
- Ponto 2
- Ponto 3
```

**Tipos de commit:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Alterações na documentação
- `style`: Alterações de formatação
- `refactor`: Refatoração
- `test`: Adição ou alteração de testes
- `chore`: Manutenção

#### Exemplo de Pull Request
```markdown
## Resumo da mudança
Breve descrição do que foi alterado.

## Motivação
Por que essa mudança foi necessária?

## Testes realizados
- [ ] Teste 1
- [ ] Teste 2
- [ ] Teste 3

## Checklist
- [ ] Código segue o estilo do projeto
- [ ] Alterações foram testadas
- [ ] Documentação foi atualizada
```

### 6. Segurança

#### Boas Práticas
- Nunca commite senhas ou chaves de API
- Use variáveis de ambiente para configurações sensíveis
- Sempre valide e sanitize inputs de usuários
- Use HTTPS em produção

#### Senhas e Chaves
```python
# ❌ NÃO FAÇA ISSO
SECRET_KEY = "minha-senha-secreta"

# ✅ FAÇA ISSO
SECRET_KEY = os.environ.get('SECRET_KEY')
```

### 7. Relatórios de Bug

#### Como Reportar
1. **Busque por duplicatas** - Verifique se o bug já foi reportado
2. **Crie um issue** - Use o template de bug report
3. **Forneça detalhes** - Inclua:
   - Versão do Python
   - Sistema operacional
   - Passos para reproduzir
   - Mensagem de erro completa

#### Template de Bug Report
```markdown
## Descrição do Bug
Descrição clara do que está acontecendo.

## Passos para Reproduzir
1. Vá para '...'
2. Clique em '....'
3. Role até '....'
4. Veja o erro

## Comportamento Esperado
Descrição do que deveria acontecer.

## Ambiente
- Sistema Operacional: [ex: Windows 10, Ubuntu 20.04]
- Python: [ex: 3.9.7]
- Versão do Projeto: [ex: 1.0.0]

## Logs de Erro
Cole aqui qualquer log ou stack trace relevante.
```

### 8. Solicitações de Funcionalidades

#### Como Solicitar
1. **Verifique necessidade** - Busque por issues similares
2. **Crie um issue** - Use o template de feature request
3. **Descreva o problema** - Explique o que falta e por quê

#### Template de Feature Request
```markdown
## Descrição da Funcionalidade
Descrição clara do que você gostaria de ver adicionado.

## Motivação
Explique por que essa funcionalidade é necessária.

## Alternativas Consideradas
Descreva alternativas que você já considerou.

## Implementação Proposta
Se possível, descreva como você imagina que a implementação deveria ser.
```

### 9. Comunicação

#### Canais de Comunicação
- **Issues**: Para bugs e solicitações de funcionalidades
- **Pull Requests**: Para contribuições de código
- **Discussions**: Para dúvidas e discussões gerais

#### Código de Conduta
- Seja respeitoso com outros contribuidores
- Seja claro e objetivo na comunicação
- Ajude outros contribuidores quando possível
- Respeite o tempo e opinião dos mantenedores

### 10. Reconhecimento

#### Como Agradecemos
- Menção nos commits
- Agradecimento no README
- Resposta rápida aos PRs
- Feedback construtivo

## Contato

Para dúvidas sobre contribuição:
- Abra uma issue
- Envie um email para: [seu-email@dominio.com]

## Agradecimentos

Agradecemos a todos os contribuidores que ajudam a melhorar este projeto!

---

**Última atualização**: Janeiro 2025
**Versão**: 1.0.0