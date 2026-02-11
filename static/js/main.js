/**
 * Validação JavaScript para o Portal Cautivo
 * Complementa a validação server-side
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const nomeInput = document.getElementById('nome');
    const emailInput = document.getElementById('email');
    const termosInput = document.getElementById('termos');
    
    // Expressão regular para validação de email
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    
    // Função para exibir mensagens de erro
    function showError(input, message) {
        const errorElement = document.getElementById(input.id + '-error');
        input.classList.add('error');
        errorElement.textContent = message;
    }
    
    // Função para limpar mensagens de erro
    function clearError(input) {
        const errorElement = document.getElementById(input.id + '-error');
        input.classList.remove('error');
        errorElement.textContent = '';
    }
    
    // Validação do nome
    nomeInput.addEventListener('blur', function() {
        const value = this.value.trim();
        if (value.length < 3) {
            showError(this, 'O nome deve ter pelo menos 3 caracteres.');
        } else {
            clearError(this);
        }
    });
    
    // Validação do email
    emailInput.addEventListener('blur', function() {
        const value = this.value.trim();
        if (!value) {
            showError(this, 'Por favor, informe seu email.');
        } else if (!emailRegex.test(value)) {
            showError(this, 'Por favor, informe um email válido.');
        } else {
            clearError(this);
        }
    });

    // Validação do checkbox de termos
    termosInput.addEventListener('change', function() {
        if (this.checked) {
            clearError(this);
        } else {
            showError(this, 'É necessário aceitar os Termos de Uso.');
        }
    });
    
    // Validação antes do envio
    form.addEventListener('submit', function(e) {
        let hasError = false;
        
        // Validar nome
        const nomeValue = nomeInput.value.trim();
        if (!nomeValue || nomeValue.length < 3) {
            showError(nomeInput, 'Por favor, informe seu nome completo.');
            hasError = true;
        } else {
            clearError(nomeInput);
        }
        
        // Validar email
        const emailValue = emailInput.value.trim();
        if (!emailValue || !emailRegex.test(emailValue)) {
            showError(emailInput, 'Por favor, informe um email válido.');
            hasError = true;
        } else {
            clearError(emailInput);
        }
        
        // Validar termos
        if (!termosInput.checked) {
            showError(termosInput, 'É necessário aceitar os Termos de Uso.');
            hasError = true;
        } else {
            clearError(termosInput);
        }
        
        // Se houver erro, impedir o envio
        if (hasError) {
            e.preventDefault();
            
            // Scroll para o primeiro erro
            const firstError = document.querySelector('.error');
            if (firstError) {
                firstError.focus();
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
    
    // Prevenir envio múltiplo
    form.addEventListener('submit', function() {
        const submitButton = this.querySelector('.btn-primary');
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="btn-text">Processando...</span><span class="btn-icon">⏳</span>';
    });
    
    // Acessibilidade: melhorar navegação por teclado
    document.querySelectorAll('input, button').forEach(function(element) {
        element.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && this.type !== 'submit') {
                e.preventDefault();
                const formElements = Array.from(form.elements).filter(el => 
                    el.tagName === 'INPUT' || el.tagName === 'BUTTON'
                );
                const currentIndex = formElements.indexOf(this);
                const nextElement = formElements[currentIndex + 1];
                
                if (nextElement) {
                    nextElement.focus();
                }
            }
        });
    });
    
    // Mensagem de confirmação visual
    if (window.location.search.includes('success=true')) {
        const successMessage = document.createElement('div');
        successMessage.className = 'alert alert-success';
        successMessage.innerHTML = '<p>✅ Cadastro realizado com sucesso! Você será redirecionado em instantes.</p>';
        document.querySelector('.form-section').insertBefore(successMessage, form);
    }
});