"use strict";

window.onload = function() {
    function showResult(str) {
        var result = document.getElementById("result");
        result.textContent = str;
    }
    
    function uploadButtonHandler() {
        var data = document.getElementById("data").value.trim();
        
        if (data.length === 0) {
            showResult("Data cannot be empty.");
            return;
        }
        
        ajaxP("POST", "upload", {"data": data})
            .then(function(data) {
                showResult("Uploaded.");
            }).catch(function(err) {
                showResult(err.message || ("An error occurred: " + err.status + " " + err.statusText));
            });
    }
    
    document.getElementById("uploadButton").addEventListener("click", uploadButtonHandler);
};
