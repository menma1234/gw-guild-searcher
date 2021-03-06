"use strict";

window.onload = function() {
    var GUILD_URL_PREFIX = "http://game.granbluefantasy.jp/#guild/detail/";
    
    var body = document.getElementById("content");
    
    function showError(str) {
        body.innerHTML = "";
        
        var span = document.createElement("span");
        span.textContent = str;
        span.className = "error";
        body.appendChild(span);
    }
    
    function createGuildLink(data, id) {
        var link = document.createElement("a");
        link.textContent = data.name;
        link.setAttribute("href", GUILD_URL_PREFIX + (id || data.id));
        
        return link;
    }
    
    function renderGuildInfo(data) {
        if (data.length === 0) {
            showError("No results found.");
            return;
        }
        
        body.innerHTML = "";
        
        data.forEach(function(entry) {
            var div = document.createElement("div");
            var ul = document.createElement("ul");
            
            for (var i = 0; i < entry.data.length; i++) {
                var elem = entry.data[i];
                
                var text = " - Ranked #" + elem.rank
                    + (elem.is_seed ? " in seed rankings " : " ")
                    + "in GW #" + elem.gw_num
                    + ((elem.points !== null && elem.points !== undefined) ? (" with " + elem.points.toLocaleString() + " points") : "");
                
                var li = document.createElement("li");
                if (i === 0) {
                    li.className = "heading";
                    
                    li.appendChild(createGuildLink(elem, entry.id));
                    li.appendChild(document.createTextNode(text));
                } else {
                    li.textContent = elem.name + text;
                }
                
                ul.appendChild(li);
            }
            
            div.appendChild(ul);
            body.appendChild(div);
        });
    }
    
    function renderGwData(data) {
        body.innerHTML = "";
        
        for (var type in data) {
            var div = document.createElement("div");
            div.className = "fullList";
        
            var span = document.createElement("span");
            span.className = "heading";
            span.textContent = (type === "regular") ? "Regular rankings:" : "Seed rankings:";
            div.appendChild(span);
            
            var ol = document.createElement("ol");
            for (var i = 0; i < data[type].length; i++) {
                var elem = data[type][i];
                
                var li = document.createElement("li");
                li.appendChild(createGuildLink(elem));
                
                if (elem.points !== null && elem.points !== undefined) {
                    li.appendChild(document.createTextNode(" - " + elem.points.toLocaleString() + " points"));
                }
                
                // there are chunks of data missing for the older ones
                li.setAttribute("value", elem.rank);
                
                ol.appendChild(li);
            }
            
            div.appendChild(ol);
            body.appendChild(div);
        }
    }
    
    function guildNameButtonHandler() {
        var name = document.getElementById("guildName").value;
        
        if (name.length === 0) {
            showError("Name cannot be empty.");
            return;
        }
        
        ajaxP("POST", "search", {"search": name})
            .then(function(data) {
                renderGuildInfo(JSON.parse(data).result);
            }).catch(function(err) {
                showError(err.message || ("An error occurred: " + err.status + " " + err.statusText));
            });
    }
    
    function guildIdButtonHandler() {
        var id = parseInt(document.getElementById("guildId").value);
        
        if (isNaN(id) || id <= 0) {
            showError("Invalid ID.");
            return;
        }
        
        ajaxP("GET", "info/" + id)
            .then(function(data) {
                renderGuildInfo([ JSON.parse(data) ]);
            }).catch(function(err) {
                showError(err.message || ("An error occurred: " + err.status + " " + err.statusText));
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
        
        ajaxP("GET", "full/" + gwNum)
            .then(function(data) {
                renderGwData(JSON.parse(data).data);
            }).catch(function(err) {
                showError(err.message || ("An error occurred: " + err.status + " " + err.statusText));
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
