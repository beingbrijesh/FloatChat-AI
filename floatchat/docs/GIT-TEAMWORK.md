Got it — here’s a **general, short and precise guide** for working on your part of the project without breaking the rest of the repo:

---

# 👩‍💻 How to Work Safely in a Team Repo

## 🔹 1. Work Only on Your Part

* Go into your folder (e.g., `app/frontend`, `app/backend`, `app/ingest`).
* Install dependencies once in repo root:

  ```bash
  python -m venv .venv
  source .venv/bin/activate   # or .venv\Scripts\activate
  pip install -r requirements.txt
  ```
* Run only your service (frontend = `streamlit`, backend = `uvicorn`, etc.).
* If another team’s code isn’t ready, use **mocks** (fake API/data) so you can still build.

---

## 🔹 2. Use Your Own Branch

* Create branch once:

  ```bash
  git checkout -b <your-role-branch>   # e.g., git checkout frontend-saini
  ```
* Save and push your changes:

  ```bash
  git add <your-folder>/
  git commit -m "Work: added feature"
  git push origin <your-role-branch>
  ```

---

## 🔹 3. Stay Updated with Main

* Pull new changes from team:

  ```bash
  git checkout main
  git pull origin main
  git checkout <your-role-branch>
  git merge main
  ```
* Do this daily or when QA announces updates.
* Resolve conflicts only if you and someone else edited the same file.

---

## 🔹 4. Don’t Break Main

* Never push directly to `main`.
* Always push to your branch → make a Pull Request → QA/lead merges after testing.

---

✅ This keeps everyone independent, avoids breaking the project, and still keeps your branch in sync.

Do you want me to also give you a **one-page Git cheatsheet** (all commands in order) that you and your teammates can copy-paste as daily routine?
