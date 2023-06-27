// $(document).ready(function () {
//     $.ajax({
//         url: "/total_projects",
//         method: "GET",
//         success: function (response) {
//             var totalProjects = response.total_projects;
//             $("#totalProjects").text(totalProjects);
//         },
//         error: function (error) {
//             console.log("Error:", error);
//         }
//     });
// });

document.addEventListener("DOMContentLoaded", function () {
    fetch("/total_projects")
        .then(response => response.json())
        .then(data => {
            var totalProjects = data.total_projects;
            document.getElementById("totalProjects").textContent = totalProjects;
        })
        .catch(error => {
            console.log("Error:", error);
        });
});

