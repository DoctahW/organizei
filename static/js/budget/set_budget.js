function openCategoryModal() {
    const modal = document.getElementById('category-modal');
    if (modal.style.display === 'none' || modal.style.display === '') {
        modal.style.display = 'block';
    } else {
        modal.style.display = 'none';
    }
}

function selectCategory(id, name) {
    document.getElementById('selected-category').value = id;
    
    const btnText = document.getElementById('category-btn').querySelector('p');
    if (btnText) {
        btnText.innerText = name;
    }
    
    document.getElementById('category-modal').style.display = 'none';
}