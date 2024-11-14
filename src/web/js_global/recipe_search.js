document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("recipe-search-form");
    const resultsContainer = document.getElementById("recipe-results");
    const recipeCountContainer = document.getElementById("recipe-count");
    const paginationContainer = document.createElement('div');
    paginationContainer.className = 'pagination-container';
    resultsContainer.parentNode.insertBefore(paginationContainer, resultsContainer.nextSibling);

    let recipes = [];
    let currentPage = getQueryParameter('page') ? parseInt(getQueryParameter('page')) : 1;
    const recipesPerPage = 10;

    const professionToItemTypes = {
        "Armouring": ["helmet", "chestplate"],
        "Tailoring": ["leggings", "boots"],
        "Weaponsmithing": ["spear", "dagger"],
        "Woodworking": ["wand", "bow", "relik"],
        "Jeweling": ["ring", "bracelet", "necklace"],
        "Alchemy": ["potion"],
        "Scribing": ["scroll"],
        "Cooking": ["food"]
    };

    const initialKeyword = getQueryParameter('keyword') || '';
    const initialProfessions = getQueryParameter('professions') ? getQueryParameter('professions').split(',') : [];
    if (initialKeyword || initialProfessions.length > 0) {
        fetchRecipes(initialKeyword, initialProfessions);
    }

    async function fetchRecipes(keyword = '', professions = []) {
        resultsContainer.innerHTML = "<p class='loading-message'>Processing results...</p>";
        applyLoadingMessageStyles();
        const recipeTypes = professions.flatMap(profession => professionToItemTypes[profession]);
        const response = await fetch("https://nori.fish/api/recipe/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ keyword, recipe_types: recipeTypes })
        });

        recipes = await response.json();
        displayResults();
        displayPagination();
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const keyword = document.getElementById("keyword").value.trim();
        const professions = Array.from(document.querySelectorAll('input[name="profession"]:checked'))
                                .map(checkbox => checkbox.value);

        if (keyword === "" && professions.length === 0) {
            resultsContainer.innerHTML = "<p class='search-warning'>Select at least a profession or Enter a keyword.</p>";
            recipeCountContainer.innerHTML = "";
            paginationContainer.innerHTML = ""; 
            return;
        }

        currentPage = 1; 
        updateURL(keyword, professions);
        await fetchRecipes(keyword, professions);
    });

    window.addEventListener('popstate', () => {
        const keyword = getQueryParameter('keyword') || '';
        const professions = getQueryParameter('professions') ? getQueryParameter('professions').split(',') : [];
        currentPage = getQueryParameter('page') ? parseInt(getQueryParameter('page')) : 1;
        fetchRecipes(keyword, professions);
    });

    function getQueryParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }

    function updateURL(keyword, professions) {
        const url = new URL(window.location);
        url.searchParams.set('keyword', keyword);
        url.searchParams.set('professions', professions.join(','));
        url.searchParams.set('page', currentPage);
        window.history.pushState({}, '', url);
    }

    function displayResults() {
        resultsContainer.innerHTML = "";
        if (recipes.length === 0) {
            resultsContainer.innerHTML = "<p class='no-results'>No results found</p>";
            paginationContainer.innerHTML = "";
            recipeCountContainer.innerHTML = "";
            return;
        }

        recipeCountContainer.innerHTML = `<span class="bold-number">${recipes.length}</span> recipes found`;

        const startIndex = (currentPage - 1) * recipesPerPage;
        const endIndex = Math.min(startIndex + recipesPerPage, recipes.length);
        const currentRecipes = recipes.slice(startIndex, endIndex);

        currentRecipes.forEach(recipe => {
            const icon = `../../resources/${recipe.type.toLowerCase()}.png`;
            const recipeElement = document.createElement("div");
            recipeElement.classList.add("recipe-card");
            recipeElement.innerHTML = `
                <img src="${icon}" alt="${recipe.name}" class="recipe-icon">
                <div class="recipe-info">
                    <h3>${recipe.name}</h3>
                    <p>${recipe.type} | ${recipe.tag}</p>
                </div>
            `;
            if (recipe.link && recipe.link.startsWith("http")) {
                recipeElement.addEventListener("click", () => {
                    window.open(recipe.link, '_blank');
                });
            } else {
                recipeElement.addEventListener("click", () => {
                    alert("Invalid recipe link.");
                });
            }

            resultsContainer.appendChild(recipeElement);
        });
    }

    function displayPagination() {
        paginationContainer.innerHTML = "";
    
        const totalPages = Math.ceil(recipes.length / recipesPerPage);
        if (totalPages <= 1) return;
    
        const maxVisiblePages = 10;
        let startPage = Math.max(currentPage - Math.floor(maxVisiblePages / 2), 1);
        let endPage = Math.min(startPage + maxVisiblePages - 1, totalPages);
    
        if (endPage - startPage < maxVisiblePages - 1) {
            startPage = Math.max(endPage - maxVisiblePages + 1, 1);
        }
    
        const createButton = (text, page) => {
            const button = document.createElement('button');
            button.innerHTML = text;
            button.disabled = page === currentPage;
            button.addEventListener('click', () => {
                currentPage = page;
                const keyword = getQueryParameter('keyword');
                const professions = getQueryParameter('professions') ? getQueryParameter('professions').split(',') : [];
                updateURL(keyword, professions);
                fetchRecipes(keyword, professions);
            });
            return button;
        };
    
        if (currentPage > 1) {
            paginationContainer.appendChild(createButton('&#x21E4;', 1));
            paginationContainer.appendChild(createButton('&#x2190;', currentPage - 1));
        }
    
        for (let i = startPage; i <= endPage; i++) {
            paginationContainer.appendChild(createButton(i, i));
        }
    
        if (currentPage < totalPages) {
            paginationContainer.appendChild(createButton('&#x2192;', currentPage + 1));
            paginationContainer.appendChild(createButton('&#x21E5;', totalPages));
        }
    }

    function applyLoadingMessageStyles() {
        const loadingMessage = document.querySelector('.loading-message');
        if (loadingMessage) {
            loadingMessage.style.textAlign = 'center';
            loadingMessage.style.fontSize = '1.5em';
        }
    }
});
