require("dotenv").config();

const express = require("express");
const bcrypt = require("bcryptjs");
const cors = require("cors");
const db = require("./config/db");

const app = express();
const PORT = process.env.PORT || 3000;

/* ===========================
   Middleware
=========================== */

app.use(cors());
app.use(express.json());
/* ===========================
   Middleware
=========================== */

app.use(cors());
app.use(express.json());


/* ===========================
   Home Route
=========================== */

app.get("/", (req, res) => {
    res.json({
        success: true,
        message: "🚀 NewEdu Backend Running"
    });
});

/* ===========================
   SIGNUP
=========================== */

app.post("/signup", (req, res) => {

    const { name, email, phone, password } = req.body;

    // Name Validation
    const nameRegex = /^[A-Za-z ]{3,50}$/;

    if (!nameRegex.test(name || "")) {
        return res.status(400).json({
            success: false,
            message: "Enter a valid name."
        });
    }

    // Email Validation
    const emailRegex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

    if (!emailRegex.test(email || "")) {
        return res.status(400).json({
            success: false,
            message: "Invalid email address."
        });
    }

    // Phone Validation
    if (!/^[0-9]{10}$/.test(phone || "")) {
        return res.status(400).json({
            success: false,
            message: "Phone number must contain exactly 10 digits."
        });
    }

    // Password Validation
    const passwordRegex =
        /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&^#()_+\-=\[\]{};':"\\|,.<>/?]).{8,}$/;

    if (!passwordRegex.test(password || "")) {
        return res.status(400).json({
            success: false,
            message:
                "Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character."
        });
    }

    // Check Existing Email
    db.query(
        "SELECT id FROM users WHERE email=?",
        [email],
        async (err, result) => {

            if (err) {
                return res.status(500).json({
                    success: false,
                    message: err.message
                });
            }

            if (result.length > 0) {
                return res.status(409).json({
                    success: false,
                    message: "Email already registered."
                });
            }

            try {

                const hashedPassword = await bcrypt.hash(password, 10);

                db.query(
                    "INSERT INTO users(name,email,phone,password) VALUES(?,?,?,?)",
                    [name, email, phone, hashedPassword],
                    (err) => {

                        if (err) {
                            return res.status(500).json({
                                success: false,
                                message: err.message
                            });
                        }

                        res.status(201).json({
                            success: true,
                            message: "Registration Successful"
                        });

                    }
                );

            } catch (error) {

                return res.status(500).json({
                    success: false,
                    message: error.message
                });

            }

        }
    );

});

/* ===========================
   LOGIN
=========================== */

app.post("/login", (req, res) => {

    const { email, password } = req.body;

    if (!email || !password) {

        return res.status(400).json({
            success: false,
            message: "Email and Password are required."
        });

    }

    db.query(
        "SELECT * FROM users WHERE email=?",
        [email],
        async (err, result) => {

            if (err) {

                return res.status(500).json({
                    success: false,
                    message: err.message
                });

            }

            if (result.length === 0) {

                return res.status(404).json({
                    success: false,
                    message: "User not found."
                });

            }

            const user = result[0];

            const match = await bcrypt.compare(password, user.password);

            if (!match) {

                return res.status(401).json({
                    success: false,
                    message: "Incorrect password."
                });

            }

            res.json({
                success: true,
                message: "Login Successful",
                user: {
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    phone: user.phone
                }
            });

        }
    );

});

/* ===========================
   Start Server
=========================== */

app.listen(PORT, () => {

    console.log("==================================");
    console.log("🚀 NewEdu Backend Started");
    console.log(`🌐 http://localhost:${PORT}`);
    console.log("==================================");

});