import threading
import subprocess


def run_server():
    subprocess.run([
        "python",
        "-m",
        "uvicorn",
        "server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "10000"
    ])


def run_bot():
    subprocess.run(["python", "medai_bot.py"])


if __name__ == "__main__":
    t1 = threading.Thread(target=run_server)
    t2 = threading.Thread(target=run_bot)

    t1.start()
    t2.start()

    t1.join()
    t2.join()