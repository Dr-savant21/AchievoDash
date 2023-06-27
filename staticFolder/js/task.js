$(document).ready(function () {
    // Show all cards by default
    $(".task .col-lg-4").show();

    // Handle navigation clicks
    $(".pagination .page-link").click(function () {
        var target = $(this).data("target"); // Get the target value

        // Show or hide cards based on the target value
        if (target === "all") {
            $(".task .col-lg-4").show();
        } else {
            $(".task .col-lg-4").hide();
            $("[data-card='" + target + "']").parent().show();
        }

        // Update active navigation link
        $(".pagination .page-item").removeClass("active");
        $(this).parent().addClass("active");

        return false; // Prevent default link behavior
    });
});

function handleStatusChange(taskId) {
    const selectElement = document.getElementById(`status-select-${taskId}`);
    const newStatus = selectElement.value;
    updateCardStatus(taskId, newStatus);
}
// Example usage when the page loads
window.addEventListener("load", function () {
    // Assuming tasks is a JavaScript array containing the task objects
    tasks.forEach(function (task) {
        updateCardStatus(task.id, task.status);
    });
});

// Example usage when adding a new task dynamically
function addNewTask(task) {
    // Assuming task is the newly added task object
    // Append the new task to the DOM

    // Update the card status
    updateCardStatus(task.id, task.status);
}
