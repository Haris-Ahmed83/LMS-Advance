from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'OK'

if __name__ == '__main__':
    app.run()
```

**Step 2 — Add `requirements.txt`:**
```
flask
gunicorn
```

**Step 3 — Add `Procfile`:**
```
web: gunicorn app:app
