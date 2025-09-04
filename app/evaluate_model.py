import openai
import json
from tqdm import tqdm
from sklearn.metrics import classification_report

from config.project_config import ProjectConfig as config
self.logger = config(logger_name="eval_model").get_logger()


# Load processed data
with open("processed_examples.json", "r", encoding="utf-8") as f:
    samples = json.load(f)


system_msg = {
    "role": "system",
    "content": "You are an AI recruiter. Decide the next recruiter action: `continue`, `schedule`, or `end`."
}

y_true = []
y_pred = []

for sample in tqdm(samples):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        messages=[
            system_msg,
            {"role": "user", "content": sample["prompt"]}
        ],
        temperature=0
    )
    if "choices" not in response or len(response["choices"]) == 0:
        self.logger.error(f"No choices returned for sample: {sample['prompt']}")
        continue
    if "message" not in response["choices"][0]:
        self.logger.error(f"No message in response for sample: {sample['prompt']}")
        continue
    if "content" not in response["choices"][0]["message"]:
        self.logger.error(f"No content in message for sample: {sample['prompt']}")
        continue
    if not isinstance(response["choices"][0]["message"]["content"], str):
        self.logger.error(f"Content is not a string for sample: {sample['prompt']}")
        continue
      
    prediction = response["choices"][0]["message"]["content"].strip().lower()
    if prediction not in ["continue", "schedule", "end"]:
        self.logger.error(f"Invalid prediction: {prediction} for sample: {sample['prompt']}")
        continue

    self.logger.info(f"Sample: {sample['prompt']}, Prediction: {prediction}")


    y_true.append(sample["label"])
    y_pred.append(prediction)

print(classification_report(y_true, y_pred))
