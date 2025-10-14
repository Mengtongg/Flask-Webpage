## Microblog-Style Flask Web
### Features
* User auth: registration, login, logout, email password reset
* Profiles: avatar, bio, last-seen, follower counts
* Posts: create, pagination
* Search: Elasticsearch full-text search on posts
* Live translation: Microsoft translation API
* Social: follow/unfollow users, personalized timeline
* Security: CSRF protection, hashed passwords
* Production-ready: .env, logging, error pages, deploy on Render

### Live Demo
- App: https://flask-webpage-3qg1.onrender.com

### Screenshots
Home Page
<img width="943" height="532" alt="Home" src="https://github.com/user-attachments/assets/b0e32e0b-661c-411f-8c62-7ec73bdac337" />
<br />
Translate Function in Explore Page
<img width="940" height="536" alt="Translate" src="https://github.com/user-attachments/assets/67be142f-107a-4c9b-956f-6905ede1c952" />
<br />
Search Function
<img width="938" height="430" alt="Search function" src="https://github.com/user-attachments/assets/6de47246-1cb5-44ec-a97c-40ebbf716605" />
<br />
Profile<br />
<img width="940" height="535" alt="Profile" src="https://github.com/user-attachments/assets/1f3e7229-adff-457b-baa3-162e6e46f5c6" />
<br />
Edit Profile<br />
<img width="959" height="526" alt="Edit profile" src="https://github.com/user-attachments/assets/267900fb-bfb9-467d-934c-f42605b9048e" />
<br />
Follow/Unfollow<br />
<img width="857" height="269" alt="Follow" src="https://github.com/user-attachments/assets/ea4acfe3-e720-4780-958e-245551f33ef9" />
<img width="863" height="296" alt="Unfollow" src="https://github.com/user-attachments/assets/de08220d-7a5a-4d86-beeb-09cdedff222f" />
<br />
Sign In<br />
<img width="944" height="477" alt="Sign in" src="https://github.com/user-attachments/assets/90381e6e-cc21-4f77-8c97-a0326d5832fa" />
<br />
Register<br />
<img width="958" height="497" alt="Regiester" src="https://github.com/user-attachments/assets/974476f2-28c1-4df3-854d-7a158c24426c" />
<br />
Password Reset<br />
<img width="955" height="311" alt="Password Reset" src="https://github.com/user-attachments/assets/d5e4a83a-cce6-47fc-8e06-5ef2a69fb786" />

### Tech Stack
-  Flask (routes,templates)
-  Flask-SQLAlchemy (ORM)
-  Flask-WTF (forms/CSRF)
-  Flask-babel (Text translation)
-  Flask-mail (emails)
-  Flask-moment (time)
-  Flask-Migrate (schema changes)
-  Flask-Login (auth)
-  Elasticsearch (Search)
-  Jinja2 (views)
-  Bootstrap (UI)
-  Gunicorn (depoly)
-  Render (deploy)

### Prerequisites
- python-3.11.9
- pip

### Project Structure
__app/ package with blueprints:__
- auth (login, logout, register, reset password)
- main (home, explore, posts, profiles, follow)
- errors (errorhandler)

### Local Developement
1. Clone & create venv
2. Create .env
3. Initialize DB
4. Flask run
   
__Search (Elasticsearch)__
- Local: if ELASTIC_HOST is set (http://localhost:9200) and ES is running, the app indexes/searches with ES.
- Render: If ES is not available: indexing is safely skipped and search falls back to a simple SQL LIKE so the UI still works. No crashes.

__Email (Password Reset)__
- Local: set EMAIL_ENABLED=1, http://localhost:8025
- Render: set EMAIL_ENABLED=0, most real email providers require a verified account (often paid or limited free tier)

__Translator (Live Translation)__
- Microsoft translator in Azure
- MS_TRANSLATOR_KEY=your-translator-key

### Deploy to Render
1. Push to GitHub
2. Pick your repo
3. Build command: pip install -r requirements.txt
4. Start command: bash start.sh
5. Manage environment

### Attribution
Built by following [<Tutorial Title/Author/Link>](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) with custom features
