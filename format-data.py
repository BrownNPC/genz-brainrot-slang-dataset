import csv
import json

# Load the dataset
def load_csv(file_path):
    dataset = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            dataset.append({
                "word": row["Slang"],
                "definition": row["Description"],
                "example": row["Example"],
                "context": row["Context"]
            })
    return dataset

# Generate prompts using the updated format
def generate_prompts(dataset):
    prompts = []
    for entry in dataset:
        prompt = (
            f"You are a professional Gen Z slang translator. Your task is to translate Gen Z slang into plain, formal English.\n\n"
            f"You will be provided with the following information:\n"
            f"- **Word**: The slang term or phrase.\n"
            f"- **Definition**: A brief explanation of what the slang means.\n"
            f"- **Example**: A sentence that demonstrates how the slang is used.\n"
            f"- **Context**: Additional information about how or where this slang is typically used.\n\n"
            f"Your job:\n"
            f"1. Carefully analyze the information provided.\n"
            f"2. Rewrite the example sentence in plain, formal English while preserving its original meaning.\n"
            f"3. Avoid including any slang or casual expressions in your response.\n\n"
            f"---\n\n"
            f"**Word**: {entry['word']}\n"
            f"**Definition**: {entry['definition']}\n"
            f"**Example**: \"{entry['example']}\"\n"
            f"**Context**: {entry['context']}\n\n"
            f"**Your Response**: Rewrite the example sentence in plain, formal English."
            f"Your response should be in the JSON format, and the key 'response' should contain the rewritten sentence."
        )
        prompts.append(prompt)
    return prompts

# Save prompts as a JSON array
def save_prompts_as_json(prompts, output_file):
    with open(output_file, mode='w', encoding='utf-8') as file:
        json.dump(prompts, file, indent=4)

# Main execution
if __name__ == "__main__":
    pass
    csv_file = "all_slangs.csv"  # Replace with the path to your CSV file
    output_file = "genz_prompts.json"
    
    dataset = load_csv(csv_file)
    prompts = generate_prompts(dataset)
    
    save_prompts_as_json(prompts, output_file)
    print(f"Prompts saved to {output_file}")
