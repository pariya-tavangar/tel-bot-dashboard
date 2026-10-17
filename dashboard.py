
from pathlib import Path
from threading import Thread, Event
from queue import Queue, Empty
from concurrent.futures import Future

from flask import Flask, jsonify, render_template_string
from playwright.sync_api import sync_playwright

# saving session seperately
PROFILE = Path(__file__).parent / "telegram_browser_profile"

app = Flask(__name__)

# Flask sends requests here. Only the browser thread touches Playwright.
request_queue = Queue()
browser_ready = Event()


def read_posts(page):
    messages = page.locator(".message")
    count = messages.count()
    posts = []
    seen = set()

    # Inspect recent message elements, newest first.
    for i in range(count - 1, max(-1, count - 31), -1):
        message = messages.nth(i)

        try:
            if not message.is_visible():
                continue

            text = message.inner_text(timeout=1500).strip()
            if text and text not in seen:
                seen.add(text)
                posts.append(text)

            if len(posts) >= 10:
                break
        except Exception:
            continue

    # Display oldest to newest.
    posts.reverse()
    return posts


def browser_worker():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            headless=False,
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://web.telegram.org/")

        print("\nTelegram Web is open.")
        print("Open your private channel and wait until its posts appear.")
        input("Press Enter here once the channel is visible... ")

        browser_ready.set()
        print("Browser connected to dashboard. Keep this terminal running.")

        while True:
            try:
                request = request_queue.get(timeout=0.5)
            except Empty:
                continue

            future = request["future"]

            try:
                if request["action"] == "posts":
                    future.set_result(read_posts(page))
                else:
                    future.set_exception(
                        ValueError("Unknown dashboard action")
                    )
            except Exception as exc:
                future.set_exception(exc)
            finally:
                request_queue.task_done()


def get_posts():
    if not browser_ready.is_set():
        raise RuntimeError(
            "Telegram browser is not ready. Check the browser terminal."
        )

    future = Future()
    request_queue.put({"action": "posts", "future": future})
    return future.result(timeout=20)


PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Telegram Channel Dashboard</title>
<style>
body {
    font-family: system-ui, sans-serif;
    max-width: 850px;
    margin: 35px auto;
    padding: 0 18px;
    background: #f4f5f8;
    color: #222;
}
h1 { font-size: 25px; }
button {
    padding: 10px 16px;
    border: 0;
    border-radius: 8px;
    background: #2678d4;
    color: white;
    cursor: pointer;
}
#status { margin: 14px 0; color: #555; }
.post {
    background: white;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 15px;
    margin: 12px 0;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}
</style>
</head>
<body>
<h1>Telegram Channel Dashboard</h1>
<p>Recent channel posts from your Telegram Web session.</p>
<button onclick="loadPosts()">Refresh posts</button>
<div id="status">Loading posts...</div>
<div id="posts"></div>

<script>
async function loadPosts() {
    const status = document.getElementById("status");
    const container = document.getElementById("posts");

    status.textContent = "Loading...";
    try {
        const response = await fetch("/posts");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Request failed");
        }

        container.replaceChildren();

        if (!data.posts.length) {
            status.textContent =
                "No posts found. Check that the channel is open in Telegram Web.";
            return;
        }

        data.posts.forEach(text => {
            const card = document.createElement("div");
            card.className = "post";
            card.textContent = text;
            container.appendChild(card);
        });

        status.textContent = data.posts.length + " message previews loaded.";
    } catch (error) {
        status.textContent = "Error: " + error.message;
    }
}

loadPosts();
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(PAGE)


@app.route("/posts")
def posts():
    try:
        return jsonify(posts=get_posts())
    except Exception as exc:
        return jsonify(error=str(exc)), 500


if __name__ == "__main__":
    Thread(target=browser_worker, daemon=True).start()

    print("Waiting for Telegram Web to be ready...")
    if not browser_ready.wait(timeout=300):
        raise RuntimeError(
            "Browser did not become ready within 5 minutes."
        )

    print("Dashboard: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
