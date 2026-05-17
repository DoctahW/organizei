(function () {
    const input = document.getElementById('value-input');
    if (!input) return;

    input.addEventListener('input', function () {
        let raw = this.value.replace(/[^\d,]/g, '');
        const parts = raw.split(',');
        let intPart = parts[0].replace(/^0+(?=\d)/, '');
        const decPart = parts.length > 1 ? ',' + parts[1].slice(0, 2) : '';
        intPart = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        this.value = intPart + decPart;
    });

    if (input.value) input.dispatchEvent(new Event('input'));

    input.closest('form').addEventListener('submit', function () {
        input.value = input.value.replace(/\./g, '');
    });
}());

const modal = document.getElementById('category-modal');
const pageTitle = document.querySelector('h2');
const categoryBtnContainer = document.querySelector('.category_btn_container');
const valueContainer = document.querySelector('.value_container');
const nameInput = document.querySelector('.name_input');
const transactionTypeSelect = document.querySelector('.transaction_type_select');
const sentTransactionBtn = document.querySelector('#sent-transaction-btn');
const addNewCategoryContainer = document.querySelector('.add-new-category-container');
const backBtn = document.getElementById('back_button');
const dateContainer = document.querySelector('.choose-date-container'); 
const recurringContainer = document.querySelector('.recurring-container');
const contaSelect = document.querySelector('select[name="conta_id"]');
const categoryLabel = document.querySelector('label[for="selected-category"]');


function closeCategoryModal() {
    if (modal) {
        backBtn.innerHTML = `<a class="back_button-link" id="back_button-link" href="/transactions" style="cursor:pointer;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"stroke-linejoin="round"><polyline points="15 18 9 12 15 6" /></svg></a>`

        modal.style.display = 'none';
        pageTitle.textContent = 'Nova Transação';
        categoryBtnContainer ? categoryBtnContainer.style.display = 'flex' : null;
        valueContainer ? valueContainer.style.display = 'flex' : null;
        nameInput ? nameInput.style.display = 'flex' : null;
        transactionTypeSelect ? transactionTypeSelect.style.display = 'block' : null;
        sentTransactionBtn ? sentTransactionBtn.style.display = 'block' : null;
        addNewCategoryContainer ? addNewCategoryContainer.style.display = 'none' : null;
        dateContainer ? dateContainer.style.display = 'flex' : null;
        recurringContainer ? recurringContainer.style.display = 'block' : null;
        contaSelect ? contaSelect.style.display = 'block' : null;
        categoryLabel ? categoryLabel.style.display = 'block' : null;
    }
};

function openCategoryModal() {
    if (modal) {

        backBtn.innerHTML = `<a class="back_button-link" id="back_button-link" onclick="closeCategoryModal()" style="cursor:pointer;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="15 18 9 12 15 6" /></svg ></a > `

        modal.style.display = 'block';
        categoryBtnContainer ? categoryBtnContainer.style.display = 'none' : null;
        valueContainer ? valueContainer.style.display = 'none' : null;
        nameInput ? nameInput.style.display = 'none' : null;
        transactionTypeSelect ? transactionTypeSelect.style.display = 'none' : null;
        sentTransactionBtn ? sentTransactionBtn.style.display = 'none' : null;
        addNewCategoryContainer ? addNewCategoryContainer.style.display = 'none' : null;
        dateContainer ? dateContainer.style.display = 'none' : null;
        recurringContainer ? recurringContainer.style.display = 'none' : null;
        contaSelect ? contaSelect.style.display = 'none' : null;
        categoryLabel ? categoryLabel.style.display = 'none' : null;
    }

    if (pageTitle) {
        pageTitle.textContent = 'Selecionar Categoria';
    }

    if (backBtn) {
        backBtn.setAttribute('href', "javascript:closeCategory()")
    }

}

function selectCategory(categoryValue, categoryLabel) {
    if (modal) {
        modal.style.display = 'none';
        pageTitle.textContent = 'Criar Transação';
        categoryBtnContainer ? categoryBtnContainer.style.display = 'flex' : null;
        valueContainer ? valueContainer.style.display = 'flex' : null;
        nameInput ? nameInput.style.display = 'flex' : null;
        transactionTypeSelect ? transactionTypeSelect.style.display = 'block' : null;
        sentTransactionBtn ? sentTransactionBtn.style.display = 'block' : null;
        addNewCategoryContainer ? addNewCategoryContainer.style.display = 'none' : null;
        dateContainer ? dateContainer.style.display = 'flex' : null;
        recurringContainer ? recurringContainer.style.display = 'block' : null;
        contaSelect ? contaSelect.style.display = 'block' : null;
        categoryLabel ? categoryLabel.style.display = 'block' : null;
    }

    const hiddenCategoryInput = document.getElementById('selected-category');
    if (hiddenCategoryInput) {
        hiddenCategoryInput.value = categoryValue;
    }

    const categoryBtn = document.getElementById('category-btn');
    if (categoryBtn) {
        categoryBtn.innerHTML = `<p>${categoryLabel}</p><span class="edit-icon">></span>`;
    }
}


function openCreateCategory() {
    if (addNewCategoryContainer) {
        addNewCategoryContainer.style.display = 'block';

        if (modal) {
            modal.style.display = 'none';

        }
    }
    //add o restante
}

function setRecurring(isRecurring) {
    const singleBtn = document.getElementById('single-btn');
    const recurringBtn = document.getElementById('recurring-btn');
    const hiddenInput = document.getElementById('is_fixed_input');

    if (!hiddenInput || !singleBtn || !recurringBtn) return; // Segurança básica

    if (isRecurring) {
        // Estilo Recorrente
        recurringBtn.style.backgroundColor = 'rgba(92, 208, 137, 0.09)';
        recurringBtn.style.border = '1px solid #5cd089';
        
        // Reseta Único
        singleBtn.style.backgroundColor = 'transparent';
        singleBtn.style.border = '1px solid transparent'; // Simplifiquei aqui
        singleBtn.style.borderTop = '1px solid var(--glass-border-top)';
        singleBtn.style.borderBottom = '1px solid var(--glass-border-bottom)';

        hiddenInput.value = 'on'; 
    } else {
        // Estilo Único
        singleBtn.style.backgroundColor = 'rgba(92, 208, 137, 0.09)';
        singleBtn.style.border = '1px solid #5cd089';
        
        // Reseta Recorrente
        recurringBtn.style.backgroundColor = 'transparent';
        recurringBtn.style.border = '1px solid transparent';
        recurringBtn.style.borderTop = '1px solid var(--glass-border-top)';
        recurringBtn.style.borderBottom = '1px solid var(--glass-border-bottom)';

        hiddenInput.value = 'off';
    }
}

// Vincula os botões à função assim que a página carregar
document.addEventListener('DOMContentLoaded', function() {
    const sBtn = document.getElementById('single-btn');
    const rBtn = document.getElementById('recurring-btn');
    if(sBtn) sBtn.onclick = () => setRecurring(false);
    if(rBtn) rBtn.onclick = () => setRecurring(true);
});

window.setRecurring = setRecurring;

const recurringSingleBtn = document.getElementById('single-btn');
const recurringRecurringBtn = document.getElementById('recurring-btn');

if (recurringSingleBtn && recurringRecurringBtn) {
    recurringSingleBtn.addEventListener('click', () => setRecurring(false));
    recurringRecurringBtn.addEventListener('click', () => setRecurring(true));
}
