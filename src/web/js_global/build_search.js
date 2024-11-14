document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("build-search-form");
    const resultsContainer = document.getElementById("build-results");
    const buildCountContainer = document.getElementById("build-count");
    const paginationContainer = document.createElement('div');
    paginationContainer.className = 'pagination-container';
    resultsContainer.parentNode.insertBefore(paginationContainer, resultsContainer.nextSibling);

    let builds = [];
    let currentPage = getQueryParameter('page') ? parseInt(getQueryParameter('page')) : 1;
    const buildsPerPage = 10;

    const initialKeyword = getQueryParameter('keyword') || '';
    const initialClassTypes = getQueryParameter('class_types') ? getQueryParameter('class_types').split(',') : [];
    if (initialKeyword || initialClassTypes.length > 0) {
        fetchBuilds(initialKeyword, initialClassTypes);
    }

    async function fetchBuilds(keyword = '', classTypes = []) {
        resultsContainer.innerHTML = "<p class='loading-message'>Processing results...</p>";
        applyLoadingMessageStyles();
        const response = await fetch("https://nori.fish/api/build/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ keyword, class_types: classTypes })
        });

        builds = await response.json();
        displayResults();
        displayPagination();
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const keyword = document.getElementById("keyword").value.trim();
        const classTypes = Array.from(document.querySelectorAll('input[name="class_type"]:checked'))
                                .map(checkbox => checkbox.value);

        if (keyword === "" && classTypes.length === 0) {
            resultsContainer.innerHTML = "<p class='search-warning'>Select at least one class or Enter a keyword.</p>";
            buildCountContainer.innerHTML = "";
            paginationContainer.innerHTML = ""; 
            return;
        }

        currentPage = 1; 
        updateURL(keyword, classTypes);
        await fetchBuilds(keyword, classTypes);
    });

    window.addEventListener('popstate', () => {
        const keyword = getQueryParameter('keyword') || '';
        const classTypes = getQueryParameter('class_types') ? getQueryParameter('class_types').split(',') : [];
        currentPage = getQueryParameter('page') ? parseInt(getQueryParameter('page')) : 1;
        fetchBuilds(keyword, classTypes);
    });

    function getQueryParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }

    function updateURL(keyword, classTypes) {
        const url = new URL(window.location);
        url.searchParams.set('keyword', keyword);
        url.searchParams.set('class_types', classTypes.join(','));
        url.searchParams.set('page', currentPage);
        window.history.pushState({}, '', url);
    }

    function displayResults() {
        resultsContainer.innerHTML = "";
        if (builds.length === 0) {
            resultsContainer.innerHTML = "<p class='no-results'>No results found</p>";
            paginationContainer.innerHTML = "";
            buildCountContainer.innerHTML = "";
            return;
        }

        buildCountContainer.innerHTML = `<span class="bold-number">${builds.length}</span> builds found`;

        const startIndex = (currentPage - 1) * buildsPerPage;
        const endIndex = Math.min(startIndex + buildsPerPage, builds.length);
        const currentBuilds = builds.slice(startIndex, endIndex);

        currentBuilds.forEach(build => {
            const buildElement = document.createElement("div");
            buildElement.classList.add("build-card");
            buildElement.innerHTML = `
                <img src="${build.icon}" alt="${build.name}" class="build-icon">
                <div class="build-info">
                    <h3>${build.name}</h3>
                    <p>${build.class} | ${build.weapon} | ${build.tag}</p>
                    <p>By ${build.credit}</p>
                </div>
            `;

            if (build.link && build.link.startsWith("http")) {
                buildElement.addEventListener("click", () => {
                    window.open(build.link, '_blank');
                });
            } else {
                buildElement.addEventListener("click", () => {
                    alert("Invalid build link.");
                });
            }

            resultsContainer.appendChild(buildElement);
        });
    }

    function displayPagination() {
        paginationContainer.innerHTML = "";
    
        const totalPages = Math.ceil(builds.length / buildsPerPage);
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
                const classTypes = getQueryParameter('class_types') ? getQueryParameter('class_types').split(',') : [];
                updateURL(keyword, classTypes);
                fetchBuilds(keyword, classTypes);
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
