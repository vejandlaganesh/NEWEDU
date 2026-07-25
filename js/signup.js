document.addEventListener("DOMContentLoaded", () => {

    const signupForm = document.getElementById("signupForm");
    const phoneInput = document.getElementById("phone");

    // Allow only numbers and limit to 10 digits
    phoneInput.addEventListener("input", function () {
        this.value = this.value.replace(/\D/g, "").slice(0, 10);
    });

    signupForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirmPassword").value;

        const nameRegex = /^[A-Za-z ]{3,50}$/;

        if (!nameRegex.test(name)) {
            alert("Please enter a valid full name.");
            return;
        }

        const emailRegex =
            /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

        if (!emailRegex.test(email)) {
            alert("Please enter a valid email address.");
            return;
        }

        const phoneRegex = /^[0-9]{10}$/;

        if (!phoneRegex.test(phone)) {
            alert("Phone number must contain exactly 10 digits.");
            return;
        }

        const passwordRegex =
            /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&^#()_+\-=\[\]{};':"\\|,.<>/?]).{8,}$/;

        if (!passwordRegex.test(password)) {
            alert(
                "Password must contain:\n\n" +
                "✔ Minimum 8 characters\n" +
                "✔ One uppercase letter\n" +
                "✔ One lowercase letter\n" +
                "✔ One number\n" +
                "✔ One special character"
            );
            return;
        }

        if (password !== confirmPassword) {
            alert("Passwords do not match.");
            return;
        }

        try {

            const response = await fetch("http://localhost:3000/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name,
                    email,
                    phone,
                    password
                })
            });

            const data = await response.json();
            if (response.ok) {
                alert("Account created successfully!");
                window.location.href = "login.html";
            } else {
                alert(data.message || "Registration failed.");
            }
        } catch (error) {
            console.error(error);
            alert("Unable to connect to the server.");
        }
    });
});