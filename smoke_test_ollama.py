import os

from ollama import Client


def main() -> None:
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

    client = Client(host=host)
    response = client.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: Clara stack is online.",
            }
        ],
    )

    print(response["message"]["content"].strip())


if __name__ == "__main__":
    main()
