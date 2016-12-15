"use strict";

window.onload = function() {
    var body = document.getElementById("content");
    
    function showError(str) {
        body.innerHTML = "";
        
        var span = document.createElement("span");
        span.textContent = str;
        span.className = "error";
        body.appendChild(span);
    }
    
    function renderGuildInfo(data) {
        if (Object.keys(data).length === 0) {
            showError("No results found.");
            return;
        }
        
        body.innerHTML = "";
        
        var pre = document.createElement("pre");
        pre.textContent = JSON.stringify(data);
        body.appendChild(pre);
    }
    
    function renderGwData(data) {
        body.innerHTML = "";
        
        var pre = document.createElement("pre");
        pre.textContent = JSON.stringify(data);
        body.appendChild(pre);
    }
    
    function guildNameButtonHandler() {
        var name = document.getElementById("guildName").value;
        
        if (name.length === 0) {
            showError("Name cannot be empty.");
            return;
        }
        
        ajaxP("POST", "/search", {"search": name})
            .then(function(data) {
                renderGuildInfo(JSON.parse(data));
            }).catch(function(err) {
                showError("An error occurred: " + err.status + " " + err.statusText);
            });
    }
    
    function guildIdButtonHandler() {
        var id = parseInt(document.getElementById("guildId").value);
        
        if (isNaN(id) || id <= 0) {
            showError("Invalid ID.");
            return;
        }
        
        ajaxP("GET", "/info/" + id)
            .then(function(data) {
                renderGuildInfo(JSON.parse(data));
            }).catch(function(err) {
                showError("An error occurred: " + err.status + " " + err.statusText);
            });
    }
    
    function gwNumButtonHandler() {
        var gwNumEntry = document.getElementById("gwNum");
        var gwNum = parseInt(gwNumEntry.value);
        var minGw = +gwNumEntry.getAttribute("min");
        var maxGw = +gwNumEntry.getAttribute("max");
        
        if (isNaN(gwNum) || gwNum < minGw || gwNum > maxGw) {
            showError("Invalid Guild Wars event number.");
            return;
        }
        
        ajaxP("GET", "/full/" + gwNum)
            .then(function(data) {
                renderGwData(JSON.parse(data));
            }).catch(function(err) {
                showError("An error occurred: " + err.statusText);
            });
    }
    
    document.getElementById("guildNameButton").addEventListener("click", guildNameButtonHandler);
    document.getElementById("guildIdButton").addEventListener("click", guildIdButtonHandler);
    document.getElementById("gwNumButton").addEventListener("click", gwNumButtonHandler);
    
    document.getElementById("guildName").addEventListener("keyup", function(e) {
        if (e.key === "Enter") {
            guildNameButtonHandler();
        }
    });
    document.getElementById("guildId").addEventListener("keyup", function(e) {
        if (e.key === "Enter") {
            guildIdButtonHandler();
        }
    });
    document.getElementById("gwNum").addEventListener("keyup", function(e) {
        if (e.key === "Enter") {
            gwNumButtonHandler();
        }
    });
};
