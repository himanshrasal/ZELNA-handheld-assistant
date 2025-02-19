import ollama


def chatWithHistory():
    messages = []
    model = "llama3.2:1b"
    maxHistory = 20

    while True:
        if len(messages) > maxHistory * 2:
            messages = messages[-(maxHistory * 2) :]

        userInput = input("you: ")

        if userInput.lower() == "quit":
            break

        messages.append({"role": "user", "content": userInput})

        try:
            response = ollama.chat(model=model, messages=messages)
            responseContent = response["message"]["content"]
            messages.append({"role": "assistant", "content": responseContent})

            print(f"model: {responseContent}")
            print(messages)

        except Exception as e:
            print(f"error while running ollama chat {e}")


# chatWithHistory()

messagearr = [
    {"role": "user", "content": "hello"},
    {
        "role": "assistant",
        "content": "Hello. Is there something I can help you with or would you like to chat?",
    },
    {"role": "user", "content": "my name is himansh"},
    {"role": "assistant", "content": "Hello Himansh, what's on your mind today?"},
    {"role": "user", "content": "i bought a tesla"},
    {
        "role": "assistant",
        "content": "Congratulations on your new Tesla, Himansh! That's exciting news. How long have you had the car for now, and do you have any plans to use it for transportation or other purposes with it?",
    },
    {"role": "user", "content": "tesla is slow "},
    {
        "role": "assistant",
        "content": "It sounds like you've noticed that the Tesla can be a bit slower than some of your other vehicles. This is normal for many electric vehicles (EVs), as they typically have a lower power-to-weight ratio and may not accelerate as quickly as gasoline-powered cars.\n\nTesla's electric motors are designed to provide a lot of torque, which helps the car get up to speed quickly. However, they can also be slower than traditional gas-powered engines because they don't have a separate combustion chamber to ignite the fuel.\n\nIf you're finding the Tesla too slow, there are a few things you can try to optimize your driving:\n\n1. Adjust your acceleration: Try shifting into higher gears earlier and accelerating more smoothly.\n2. Use regenerative braking: This feature captures some of the kinetic energy and converts it back into electrical energy, which can help improve efficiency and reduce wear on the brakes.\n3. Drive more efficiently: Keep an eye on your speedometer and try to drive within your comfort zone – avoiding sudden acceleration or hard braking can help improve fuel efficiency.\n\nDo you have any specific concerns about driving your Tesla that I can help with?",
    },
]


def parseOllamaMessageArrayToJson(messages):
    data = []
    for message in messages:
        if message.get("role") == "assistant":
            data.append({"sender": "server", "message": message.get("content")})
        if message.get("role") == "user":
            data.append({"sender": "client", "message": message.get("content")})


parseOllamaMessageArrayToJson(messagearr)
