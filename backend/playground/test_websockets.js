{
    let webSocket = new WebSocket('ws://localhost:8000/ws');
    let last_time = 0;

    webSocket.onopen = function() {
        console.log("WebSocket is open now.");
        webSocket.send("test");
    };

    webSocket.onmessage = function(e) {
        json_data = JSON.parse(e.data);
        console.log("Message received:", json_data['time'], 'time taken to receive:', (json_data['time'] - last_time) / 1000, 'seconds');
        last_time = json_data['time'];
    };

    webSocket.onerror = function(error) {
        console.error("WebSocket error:", error);
    };

    webSocket.onclose = function() {
        console.log("WebSocket is closed.");
    };
}
