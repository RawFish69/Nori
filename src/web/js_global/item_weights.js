function displayWeights(result) {
    const resultsContainer = document.getElementById("analysis-results");

    const scales = result.scales || {};
    const weights = result.weights || {};

    if (Object.keys(scales).length > 0 && Object.keys(weights).length > 0) {
        const scalesContainer = document.createElement("div");
        scalesContainer.classList.add("scales-container");

        const sortedScales = Object.entries(weights).sort((a, b) => b[1] - a[1]);

        for (const [scale, weight] of sortedScales) {
            const scaleItem = document.createElement("div");
            scaleItem.classList.add("scale-item");
            scaleItem.innerHTML = `<span style="font-weight: bold">${scale} Scale :</span> <span style="color:${getRateColor(weight)}">${weight}%</span>`;
            scaleItem.addEventListener("click", () => {
                const content = document.getElementById(`scale-content-${scale}`);
                content.classList.toggle("show");
            });
            scalesContainer.appendChild(scaleItem);

            const scaleContentElement = document.createElement("div");
            scaleContentElement.classList.add("scale-content");
            scaleContentElement.id = `scale-content-${scale}`;
            scaleContentElement.innerHTML = `<strong>${scale} Scale Weight Distribution</strong><br>`;
            for (const stat in scales[scale]) {
                if (scales[scale][stat] !== null) {
                    const scaleStatElement = document.createElement("p");
                    scaleStatElement.innerHTML = `${mapping[stat]}: ${scales[scale][stat]}%`;
                    scaleContentElement.appendChild(scaleStatElement);
                }
            }
            scalesContainer.appendChild(scaleContentElement);
        }

        resultsContainer.appendChild(scalesContainer);

        const noteElement = document.createElement("p");
        noteElement.classList.add("note");
        noteElement.innerHTML = "<i>The weight scale measures the effectiveness of an item; an item may have multiple scales.</i>";
        resultsContainer.appendChild(noteElement);
    }
}
