"use strict";

function ajaxP(method, url, data) {
    return new Promise(function(res, rej) {
        var xhr = new XMLHttpRequest();
        xhr.open(method, url);
        
        xhr.onload = function() {
            res(xhr.response);
        };
        
        xhr.onerror = function() {
            rej({
                "status": xhr.status,
                "statusText": xhr.statusText
            });
        };
        
        xhr.send(data);
    });
}
