document.addEventListener("DOMContentLoaded", function () {
    const modelSelector = document.getElementById("model-selector");
    const selectedModelInput = document.getElementById("selected-model");

    if (modelSelector && selectedModelInput) {
        modelSelector.addEventListener("change", function () {
            selectedModelInput.value = modelSelector.value;
        });
    }
});
