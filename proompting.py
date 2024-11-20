import json
import os
import requests
import time
import signal

# Terminal colors
black = "\033[0;30m"
red = "\033[0;31m"
green = "\033[0;32m"
yellow = "\033[0;33m"
white = "\033[0;37m"
nocolor = "\033[0m"

# API configuration
API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/YOUR-ACCOUNT-ID/ai/run/"
headers = {"Authorization": "Bearer TOKEN"}

# Function to call the AI model
def run(model, prompt):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": prompt}
    ]
    data = {"messages": messages}
    response = requests.post(f"{API_BASE_URL}{model}", headers=headers, json=data)
    return response.json()

# Graceful shutdown handler
def save_data(processed_data):
    try:
        with open("normal_data.json", mode='r+', encoding='utf-8') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []  # If the file is empty or corrupted, start with an empty list

            # Append the processed data to the existing data
            existing_data.extend(processed_data)

            # Truncate and overwrite with updated data
            file.seek(0)
            json.dump(existing_data, file, indent=4)
            file.truncate()

        print(f"{green}Data has been saved successfully to 'normal_data.json'.{nocolor}")
    except Exception as e:
        print(f"{red}Error saving data: {e}{nocolor}")

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print(f"\n{red}Script interrupted. Saving data...{nocolor}")
    save_data(processed_data)
    exit(0)

# Register the signal handler for keyboard interrupt (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    # Load the data
    with open("genz_prompts.json", mode='r', encoding='utf-8') as file:
        prompts = json.load(file)

    with open("original_examples.json", mode='r', encoding='utf-8') as file:
        original_examples = json.load(file)

    processed_data = []  # Store results temporarily

    for i, prompt in enumerate(prompts):
        while True:
            try:
                # Call the AI model
                output = run("@cf/meta/llama-3-8b-instruct", prompt)
                response = output.get('result', {}).get('response')
                if not response:
                    raise ValueError("No response received from the API.")
                r = json.loads(response)  # Decode response JSON
            except Exception as e:
                print(f"{red}Error with the AI model: {e}{nocolor}")
                print(f"{yellow}Retrying...{nocolor}")
                time.sleep(1)  # Add a small delay before retrying
                continue  # Retry if the API call fails

            # Display the original example and translation
            print(f"{yellow}Original Example:{nocolor} {original_examples[i]}")
            print(f"{green}Translation:{nocolor} {r['response']}\n")

            # Ask the user to save or retry
            save = input(f"{white}Save this prompt? (y/n): {nocolor}").strip().lower()
            
            # Append data whether or not the user wants to save
            processed_data.append({
                "role": "user",
                "content": original_examples[i]
            })
            processed_data.append({
                "role": "assistant",
                "content": r['response']
            })

            # Save data frequently (after each prompt)
            save_data(processed_data)

            if save == "y":
                print(f"{green}Data has been saved successfully to 'normal_data.json'.{nocolor}")
                os.system("clear")
                print(f"We are on prompt: {i + 1} / {len(prompts)}")
                processed_data.clear()  # Clear the processed data list after saving
                break
            else:
                print(f"{red}Retrying this prompt...{nocolor}")
                os.system("clear")
                continue  # Retry if the user isn't satisfied

    # Final save at the end of the script
    save_data(processed_data)
