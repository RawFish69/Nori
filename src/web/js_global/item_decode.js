document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("item-analysis-form");
    const resultsContainer = document.getElementById("analysis-results");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const encodedItem = document.getElementById("encoded-item").value.trim();

        if (encodedItem === "") {
            resultsContainer.innerHTML = "<p class='search-warning'>Please enter an encoded item.</p>";
            return;
        }

        try {
            const response = await fetch("https://nori.fish/api/item/analysis", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ encoded_item: encodedItem })
            });

            const data = await response.json();
            displayResults(data.Result);
        } catch (error) {
            console.error("Error analyzing item:", error);
            resultsContainer.innerHTML = "<p class='search-warning'>An error occurred. Please try again later.</p>";
        }
    });
});
