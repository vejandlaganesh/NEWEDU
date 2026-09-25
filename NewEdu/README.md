# NewEdu 🎓

> **Learn Today • Build Skills • Shape Your Future**

NewEdu is an AI-powered education platform designed to provide students with a more practical, personalized, and skill-oriented learning experience.

The platform supports students, teachers, parents, and administrators through dedicated dashboards and workflows. It combines academic learning, assignments, quizzes, progress tracking, notifications, and AI-powered assistance in one platform.

---

## 🚀 Key Features

### 👨‍🎓 Student Portal

Students can:

* Access their personalized dashboard
* View subjects and academic content
* Explore chapters and lessons
* Access learning materials
* Complete assignments
* Submit assignment files or text
* Take quizzes
* View quiz results
* Track academic performance
* Access AI Assistant
* Receive notifications
* Manage profile and account settings

### 👨‍🏫 Teacher Portal

Teachers can:

* View assigned classes and subjects
* View students
* Upload learning materials
* Create and manage chapters and lessons
* Create assignments
* Review student submissions
* Grade assignments
* Create quizzes
* Add quiz questions
* Publish quizzes
* View reports
* Use AI-powered teaching tools
* Generate AI learning content
* Generate AI quizzes
* Save AI-generated content
* Manage profile and settings

### 👨‍👩‍👧 Parent Portal

Parents can:

* View their dashboard
* Monitor student assignments
* View quizzes
* View quiz results
* View academic reports
* View student results
* Receive notifications
* Manage profile
* Manage account settings

### 🛠️ Admin Dashboard

Administrators can manage the complete platform.

#### User Management

* View users
* Create users
* Activate/deactivate users
* Manage user roles

#### Academic Management

* Academic years
* Classes
* Sections
* Subjects
* Class-subject mapping
* Chapters
* Lessons

#### Content Management

* Learning materials
* Assignments
* Quizzes
* Results
* Reports

#### Platform Management

* Notifications
* System settings
* Administrative dashboard

---

# 🤖 AI Features

NewEdu integrates AI capabilities into the learning platform.

### AI Student Assistant

Students can interact with an AI assistant for learning support.

Features include:

* AI conversations
* Conversation history
* Conversation archiving
* AI-generated explanations
* Personalized learning assistance
* AI recommendations

### AI Recommendations

The system can generate personalized recommendations based on student performance.

Recommendations can contain:

* Strengths
* Weaknesses
* Learning advice
* Related subjects
* Related chapters
* Performance source data

### AI Teacher Tools

Teachers can use AI to:

* Generate educational content
* Generate quizzes
* Create learning material ideas
* Save generated content
* Build AI-assisted learning resources

---

# 📚 Learning System

NewEdu organizes academic content using a structured hierarchy:

```text
Academic Year
     │
     ├── Class
     │    │
     │    ├── Section
     │    │
     │    └── Subjects
     │          │
     │          ├── Chapters
     │          │     │
     │          │     └── Lessons
     │          │
     │          └── Learning Materials
```

Learning materials can include:

* PDF
* Documents
* Images
* Videos
* External links
* Text content

Uploaded learning materials have validation for file type and file size.

---

# 📝 Assignments

Teachers can create assignments containing:

* Title
* Description
* Academic year
* Class
* Subject
* Section
* Chapter
* Due date
* Maximum score
* Optional attachment

Students can submit:

* Text responses
* File attachments

Assignment submissions support statuses such as:

```text
PENDING
   ↓
SUBMITTED
   ↓
GRADED
```

Teachers can provide:

* Marks
* Feedback
* Submission evaluation

---

# 🧠 Quiz System

NewEdu provides a complete quiz workflow.

Teachers can:

1. Create a quiz
2. Select class and subject
3. Select a chapter
4. Set duration
5. Set passing score
6. Set maximum attempts
7. Add questions
8. Publish the quiz

Students can:

1. View available quizzes
2. Start a quiz
3. Answer questions
4. Submit the attempt
5. View the result

The quiz system also tracks:

* Attempt number
* Start time
* Expiration time
* Completion status
* Scores

Quiz questions cannot be modified after attempts have been made, helping preserve result integrity.

---

# 🔔 Notification System

NewEdu includes an internal notification system.

Notification types include:

* Assignment
* Quiz
* Result
* Learning Material
* AI Recommendation
* System

Users can:

* View notifications
* Open related pages
* Mark individual notifications as read
* Mark all notifications as read

Unread notification counts are also available throughout the application.

---

# 🔐 Authentication & Authorization

NewEdu uses a custom authentication system based on email addresses.

Supported roles:

```text
STUDENT
TEACHER
PARENT
ADMIN
```

Users authenticate using:

* Email
* Password

The platform also provides:

* Registration
* Login
* Logout
* Password change
* Password reset
* Password reset confirmation

Role-based access control prevents users from accessing functionality outside their assigned role.

---

# 🔎 Global Search

NewEdu includes a global search module to help users find relevant platform content quickly.

---

# 🗂️ Project Structure

```text
NewEdu/
│
├── apps/
│   │
│   ├── accounts/
│   │   ├── models.py
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── decorators.py
│   │   └── urls.py
│   │
│   ├── academics/
│   │   ├── models.py
│   │   └── views.py
│   │
│   ├── students/
│   │   ├── models.py
│   │   ├── forms.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── teachers/
│   │   ├── models.py
│   │   ├── forms.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── parents/
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── content/
│   │   ├── models.py
│   │   ├── forms.py
│   │   └── views.py
│   │
│   ├── assignments/
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── quizzes/
│   │   ├── models.py
│   │   ├── forms.py
│   │   ├── services.py
│   │   └── views.py
│   │
│   ├── reports/
│   │   ├── models.py
│   │   ├── services.py
│   │   └── views.py
│   │
│   ├── notifications/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── views.py
│   │   └── context_processors.py
│   │
│   ├── ai_assistant/
│   │   ├── models.py
│   │   ├── services/
│   │   ├── management/
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── search/
│   │   ├── models.py
│   │   ├── services.py
│   │   └── views.py
│   │
│   └── core/
│       ├── models.py
│       ├── forms.py
│       ├── views.py
│       └── management/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── templates/
│
├── static/
│
├── media/
│
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🛠️ Technology Stack

### Backend

* Python
* Django 5.2

### Database

* MySQL
* MySQL Client

### AI

* Google GenAI
* Configurable AI model through environment variables

### Frontend

* HTML5
* CSS3
* JavaScript
* Django Templates

### Data & Validation

* Pydantic
* Django Forms
* Django ORM

---

# ⚙️ Requirements

Make sure the following are installed:

```text
Python 3.11+
MySQL 8.0+
pip
Git
```

---

# 📦 Installation

## 1. Clone the Repository

```bash
git clone <your-repository-url>
cd NewEdu
```

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Configuration

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=newedu
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
DB_PORT=3306

AI_API_KEY=your-ai-api-key
AI_MODEL=gemini-1.5-pro

AI_MAX_MESSAGE_LENGTH=2000
AI_MAX_HISTORY_MESSAGES=10
```

> Never commit your real `.env` file or API keys to GitHub.

---

# 🗄️ Database Setup

Create the MySQL database:

```sql
CREATE DATABASE newedu;
```

Then run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

# 🌱 Seed Demo Data

The project includes a development seed command.

Run:

```bash
python manage.py seed_data
```

This creates or updates safe local demo data and Class 10 learning data for development.

---

# 👤 Create Admin Account

Create a Django superuser:

```bash
python manage.py createsuperuser
```

Enter:

```text
Email:
Password:
```

Then access:

```text
http://127.0.0.1:8000/admin/
```

---

# 🤖 AI Health Check

The project includes an AI health-check management command.

Run:

```bash
python manage.py ai_healthcheck
```

Use this to verify that the configured AI service is available.

---

# ▶️ Run the Application

Start the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

# 🌐 Main Routes

| Area              | URL                   |
| ----------------- | --------------------- |
| Home              | `/`                   |
| Login             | `/accounts/login/`    |
| Register          | `/accounts/register/` |
| Admin             | `/admin/`             |
| Admin Dashboard   | `/admin-dashboard/`   |
| Student Dashboard | `/student/dashboard/` |
| Teacher Dashboard | `/teacher/dashboard/` |
| Parent Dashboard  | `/parent/dashboard/`  |
| AI API            | `/ai/api/`            |
| Notifications     | `/notifications/`     |
| Search            | `/search/`            |

---

# 🔄 Platform Workflow

```text
                    NEWEDU
                       │
          ┌────────────┴────────────┐
          │                         │
       Register                   Login
          │                         │
          └────────────┬────────────┘
                       │
                 Role Detection
                       │
       ┌───────────────┼────────────────┐
       │               │                │
    Student         Teacher           Parent
       │               │                │
       │               │                │
  Learning        Create Content    Monitor Student
  Assignments     Assignments       Results
  Quizzes         Quizzes           Reports
  AI Assistant    AI Tools          Notifications
  Results         Reports
       │               │
       └───────────────┼───────────────┘
                       │
                  AI Assistance
                       │
                Personalized
                Recommendations
```

---

# 🔒 Security Features

The platform includes several security-oriented implementations:

* Custom email-based authentication
* Role-based access control
* Django CSRF protection
* Password validation
* Secure file download handling
* File extension validation
* File size validation
* Database constraints
* Quiz attempt protection
* Production security settings
* Secure session and CSRF cookies in production
* HSTS configuration in production
* `X-Frame-Options` protection

---

# 📁 File Upload Limits

Learning materials:

```text
Maximum size: 25 MB
```

Supported learning-material formats include:

```text
PDF
DOC
DOCX
TXT
PNG
JPG
JPEG
MP4
WEBM
PPT
PPTX
```

Assignment/submission files:

```text
Maximum size: 10 MB
```

Supported formats include:

```text
PDF
DOC
DOCX
TXT
PNG
JPG
JPEG
CSV
```

---

# 🧪 Testing

The project contains tests across multiple applications, including:

* Accounts
* Students
* Teachers
* Parents
* Assignments
* Quizzes
* Notifications
* AI Assistant
* Search
* Reports
* Security-related functionality

Run the complete test suite with:

```bash
python manage.py test
```

---

# 🏗️ Architecture

NewEdu follows a modular Django architecture.

```text
                    ┌───────────────┐
                    │   Frontend    │
                    │ HTML/CSS/JS   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Django Views  │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Business Logic   Services       Forms
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    ┌───────────────┐
                    │ Django ORM    │
                    └───────┬───────┘
                            │
                            ▼
                       MySQL Database

                            │
                            ▼
                    ┌───────────────┐
                    │  AI Service   │
                    │ Google GenAI  │
                    └───────────────┘
```

---

# 🎯 Project Goals

NewEdu aims to move beyond traditional exam-focused education by combining:

* Concept learning
* Practical learning
* Soft skills
* AI-assisted learning
* Leadership development
* Career discovery
* Personalized recommendations

The platform is designed to support students throughout their academic journey while giving teachers and parents the tools required to support their progress.

---

# 🚧 Future Enhancements

Potential future improvements include:

* Personalized AI learning paths
* Advanced career recommendation engine
* AI-powered study plans
* Student performance prediction
* More interactive learning activities
* Gamification and achievement badges
* Advanced analytics dashboards
* Mobile application
* Real-time teacher-student communication
* Expanded career discovery system
* AI-powered doubt solving
* Learning streaks and progress milestones

---

# 👨‍💻 Development

This project is organized as a modular Django application so that new features can be added without restructuring the complete platform.

When adding a new feature:

1. Create or update the appropriate app.
2. Add models where required.
3. Create migrations.
4. Add forms and validation.
5. Implement views/services.
6. Configure URLs.
7. Add templates.
8. Add tests.
9. Run migrations.
10. Verify role-based permissions.

---

# 📄 License

This project is currently intended for educational and development purposes.

Add your preferred license here if the project is published publicly.

---

# 👤 Author

**V. Ganesh**

AI & ML | Python | Django | Data Science

GitHub:
`https://github.com/vejandlaganesh`

---

## ⭐ NewEdu

**Learn Today • Build Skills • Shape Your Future**