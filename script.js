const API_URL = "http://localhost:8000/api/chat";

const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const chatMessages = document.getElementById("chatMessages");

// Display messages in chatbot
function displayMessage(message, sender) {
    const messageDiv = document.createElement("div");

    messageDiv.className = sender;
    messageDiv.textContent = message;

    chatMessages.appendChild(messageDiv);
}

// Send message to Python REST API
async function sendMessage() {

    const message = messageInput.value.trim();

    if (message === "") {
        return;
    }

    displayMessage(message, "user-message");

    messageInput.value = "";
    sendBtn.disabled = true;

    try {
        const response = await fetch(API_URL, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })
        });

        if (!response.ok) {
            throw new Error("API connection failed");
        }

        const data = await response.json();

        displayMessage(
            data.reply,
            "bot-message"
        );

    } catch (error) {

        console.error(error);

        displayMessage(
            "Sorry! Unable to connect to Institute 360 server.",
            "bot-message"
        );

    } finally {
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

// Send button click
sendBtn.addEventListener("click", sendMessage);

// Send message using Enter key
messageInput.addEventListener("keydown", function(event) {

    if (event.key === "Enter") {
        sendMessage();
    }

});