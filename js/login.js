const response = await fetch("http://localhost:3000/login", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        email,
        password
    })
});

const data = await response.json();

if (data.success) {

    // Save logged-in user
    localStorage.setItem("user", JSON.stringify(data.user));

    alert("Login Successful!");

    // Redirect to dashboard
    window.location.href = "../dashboard.html";

} else {

    alert(data.message);

}