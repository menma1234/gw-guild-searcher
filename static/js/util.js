"use strict";

function ajaxP(method, url, data) {
    return new Promise(function(res, rej) {
        var xhr = new XMLHttpRequest();
        xhr.open(method, url);
        
        xhr.onload = function() {
            if (xhr.status >= 400) {
                xhr.onerror();
            } else {
                res(xhr.response);
            }
        };
        
        xhr.onerror = function() {
            rej({
                "status": xhr.status,
                "statusText": xhr.statusText
            });
        };
        
        if (typeof data === "object") {
            data = JSON.stringify(data);
        }
        
        xhr.send(data);
    });
}
