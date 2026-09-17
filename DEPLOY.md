# Deploying the App

This application is built with **Python**, **Flask**, and **SQLite**. Because it has a Python backend and uses a local SQLite database, it cannot be hosted on static sites like GitHub Pages or Netlify. It requires a server capable of running Python.

The easiest, free platform to deploy this app is **Render**. 

## Option A: Deploy to Render (Recommended for prototypes)

Render offers a generous free tier for Web Services and deploys directly from your GitHub repository.

1. **Push your code to GitHub**
   Make sure all your code is pushed to a public GitHub repository. Ensure `requirements.txt` includes `gunicorn` (which it does) and `app.py` is ready.

2. **Connect to Render**
   - Go to [Render.com](https://render.com/) and sign in with GitHub.
   - Click **New +** -> **Web Service**.
   - Select **"Build and deploy from a Git repository"**.
   - Connect your GitHub account and select your repository.

3. **Configure the Service**
   - **Name:** Your choice (e.g., `feeder-van-board`)
   - **Region:** Choose whatever is closest to you.
   - **Branch:** `main` (or `master`)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`

4. **Deploy**
   Click **Create Web Service**. Render will install dependencies and start the app. Your live URL will appear at the top left.

> [!WARNING]
> **A note on SQLite and Render Free Tier:**
> The Render free tier spins down your server after 15 minutes of inactivity. When it wakes back up, it uses a fresh disk image. **This means your SQLite database will reset to zero every time the app spins down.** This is perfectly fine for a prototype or demo! If you need persistent data later, you can upgrade Render or use a hosted PostgreSQL database.

## Option B: Deploy to PythonAnywhere (Free persistent data)

If you want your SQLite database to persist forever without paying, [PythonAnywhere](https://www.pythonanywhere.com/) is a great alternative.

1. Create a free "Beginner" account.
2. Under the **Web** tab, click **Add a new web app**.
3. Choose **Flask** and select your Python version.
4. Open a **Bash Console** and clone your GitHub repository into your files.
5. In the **Web** tab, update the **Source code** directory and configure the WSGI file to point to your `app.py`.
6. Reload the web app, and it will be live at `yourusername.pythonanywhere.com` with fully persistent SQLite data.
