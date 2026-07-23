// Phase 3 — live notifications over SocketIO.
(function () {
    // Connect to the same origin; the session cookie identifies the user
    // so the server's connect handler can room us correctly.
    const socket = io();

    socket.on("connect", function () {
        console.log("realtime: connected");
    });

    socket.on("connect_error", function (err) {
        console.warn("realtime: connect_error", err.message);
    });

    socket.on("disconnect", function (reason) {
        console.log("realtime: disconnected —", reason);
    });

    // A new notification pushed just to this user.
    socket.on("notification", function (data) {
        bumpBadge();
        showToast(data.message);
    });

    // Increment the bell badge by 1.
    function bumpBadge() {
        const badge = document.getElementById("bell-badge");
        if (!badge) return;  // managers don't have a bell — that's fine
        const current = parseInt(badge.textContent.trim() || "0", 10);
        badge.textContent = current + 1;
        badge.style.display = "inline-block";
    }

    // Floating toast pop-up, auto-dismisses after 6s.
    function showToast(message) {
        let container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            document.body.appendChild(container);
        }
        const toast = document.createElement("div");
        toast.className = "toast";
        toast.textContent = message;
        container.appendChild(toast);
        // Force reflow so the CSS transition fires.
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                toast.classList.add("show");
            });
        });
        setTimeout(function () {
            toast.classList.remove("show");
            setTimeout(function () { toast.remove(); }, 300);
        }, 6000);
    }
})();
