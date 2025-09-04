import time
import json
import os

from config.project_config import ProjectConfig
self.logger = ProjectConfig().get_logger()

# file: fine_tune/sample_set_classifier.py
# Generates a training set for classifying conversation labels in a job interview chatbot.



# Define the system prompt for the classification task
SYSTEM_PROMPT = """
You are a classification engine for recruiter messages in a job interview chatbot. 
Your task is to determine the intent behind the recruiter's message and return one of these labels:

- continue_ask_question: Recruiter is asking the candidate about skills, experience, availability, etc.
- continue_answer_question: Recruiter is responding to a candidate's question about the job or company.
- schedule_offer_slots: Recruiter offers multiple time slots for interview scheduling.
- schedule_set_slot: Recruiter proposes or confirms a specific interview slot.
- schedule_cancel: Recruiter cancels or acknowledges cancellation of a scheduled interview.
- end_with_schedule: Recruiter ends the conversation after setting or confirming a schedule.
- end_no_schedule: Recruiter ends the conversation without setting a schedule or after cancellation.

Only return the label, without explanation or punctuation.

Examples:
Candidate: Please remove me from your list.
Recruiter: No worries—I appreciate the update. Take care!
Label: end_no_schedule

Candidate: I'd be happy to schedule.
Recruiter: What about Tuesday at 10 AM or Wednesday at 2 PM?
Label: schedule_offer_slots

Candidate: Monday at 3 PM works for me.
Recruiter: Monday at 3 PM is set. Have a great day!
Label: end_with_schedule
"""


class SampleSetClassifier:

    def __init__(self, client=None, model=None):
           """
              Initializes the SampleSetClassifier with an OpenAI client and model.
                :param client: An instance of OpenAI client.
                :param model: The OpenAI model to use for classification.
                :raises ValueError: If the model is not supported.
            """
           if client is None:
               client = ProjectConfig().get_client()
           if model is None:
               model = ProjectConfig().get_model()

           self.client = client
           self.model = model
           self.system_prompt = SYSTEM_PROMPT

    
    def classify_turn(self, candidate_text, recruiter_text):
        user_message = f"Candidate: {candidate_text}\nRecruiter: {recruiter_text}\nLabel:"
        self.logger.info(f"Classifying turn: {user_message[:60]}...")  # Log the first 60 characters for brevity
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0
        )
        res = response.choices[0].message.content.strip()
        self.logger.debug(f"Model result: {res}")
        return res

    def classify_samples(self, convs):
        """
        Classifies a list of sample conversations using the OpenAI model.
        :param convs: A list of dictionaries with 'input' and 'label' keys.
        :return: A list of dictionaries with 'input', 'predicted_label', and 'label'.
        """
        results = []
        for i, conv in enumerate(convs):
            if not isinstance(conv, dict) or "turns" not in conv:
                self.logger.error(f"Invalid sample format at index {i}: {conv}")
                continue
            
            # Extract the recruiter turn from the sample
            if not isinstance(conv["turns"], list) or len(conv["turns"]) == 0:
                self.logger.error(f"No turns found in sample at index {i}: {conv}")
                continue
            if len(conv["turns"]) < 2:
                self.logger.error(f"Not enough turns to classify at index {i}: {conv}")
                continue
            # Assuming the last turn is the recruiter turn
            if not isinstance(conv["turns"][0], dict) or "speaker" not in conv["turns"][0] or "text" not in conv["turns"][0]:
                self.logger.error(f"Invalid turn format at index {i}: {conv['turns'][0]}")
                continue
            if conv["turns"][-1]["speaker"] != "recruiter":
                self.logger.error(f"Last turn is not a recruiter turn at index {i}: {conv['turns'][-1]}")
                continue
            
            turns = conv["turns"]
            for i, turn in enumerate(turns):
                if turn["speaker"] != "recruiter":
                    continue
                
                label = turn["label"] or "unknown"
                recruiter_msg = turn["text"]
                candidate_prev = turns[i-1]["text"] if i > 0 and turns[i-1]["speaker"] == "candidate" else ""
                

                if not recruiter_msg:
                    self.logger.error(f"Recruiter message is empty at index {i}: {conv['turns'][-1]}")
                    continue
                
                self.logger.info(f"Classifying turn {i}: Candidate: {candidate_prev[:60]}... | Recruiter: {recruiter_msg[:60]}...")
                try:
                    
                    new_label = self.classify_turn(candidate_prev, recruiter_msg)
                    self.logger.debug(f"Labels for {recruiter_msg[:60]} : Original Label: {label}, New Label: {new_label}")
                    results.append({
                        "input": f"Candidate: {candidate_prev}\nRecruiter: {recruiter_msg}",
                        "predicted_label": new_label,
                        "label": label
                    })                   
                    time.sleep(1)

                except Exception as e:
                    self.logger.error(f"Error classifying turn {i}: {e}")                
                    results.append({
                        "input": f"Candidate: {candidate_prev}\nRecruiter: {recruiter_msg}",
                        "predicted_label": "error",
                        "label": label
                    })
        return results
    #end def classify_samples

    def save_results(self, results, output_file):
        """
        Saves the classification results to a JSON file.
        :param results: A list of classification results.
        :param output_file: The file path to save the results.
        """
        if not results:
            self.logger.warning("No results to save.")
            return
        if not output_file:
            raise ValueError("Output file path must be provided.")
        self.logger.info(f"Saving results to {output_file}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        if not output_file.endswith('.jsonl'):
            self.logger.warning(f"Output file {output_file} does not have .jsonl extension, appending it.")
            output_file += '.jsonl'
        self.logger.info(f"Writing results to {output_file}")
        # Save results in JSONL format
        with open(output_file, 'w', encoding='utf-8') as fout:
            for res in results:
                json.dump({
                    "messages": [
                        {"role": "system", "content": "You are an AI recruiter. Based on the candidate message and recruiter response, classify the recruiter intent."},
                        {"role": "user", "content": res["input"]},
                        {"role": "assistant", "content": res["predicted_label"]}
                    ]
                }, fout)
                fout.write("\n")
        print(f"Results saved to {output_file}")
    #end def save_results

    def load_samples(self, input_file):
        """
        Loads samples from a JSON file.
        :param input_file: The file path to load samples from.
        :return: A list of samples.
        """
        if not input_file:
            raise ValueError("Input file path must be provided.")
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file {input_file} does not exist.")
        
        self.logger.info(f"Loading samples from {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            samples = json.load(f)
        if not isinstance(samples, list):
            raise ValueError(f"Expected a list of samples in {input_file}, got {type(samples)}")
        if not samples:
            self.logger.warning(f"No samples found in {input_file}")
            return []
        self.logger.info(f"Loaded {len(samples)} samples from {input_file}")
        return samples
    #end def load_samples

    def generate_training_set(self, input_file, output_file) -> list:
        """
        Runs the classification process: loads samples, classifies them, and saves the results.
        :param input_file: The file path to load samples from.
        :param output_file: The file path to save the classification results.
        """
        self.logger.info(f"Running classification with model: {self.model}")
        if not input_file:
            raise ValueError("Input file path must be provided.")
        if not output_file:
            raise ValueError("Output file path must be provided.")

        # Check if the input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file {input_file} does not exist.")

        self.logger.info(f"Loading samples from {input_file}")
        samples = self.load_samples(input_file)
        if not samples:
            self.logger.warning("No samples to classify.")
            return
       
        if not isinstance(samples, list):
            self.logger.error(f"Expected a list of samples, got {type(samples)}")
            return

        results = self.classify_samples(samples)
        self.logger.info(f"Got {len(results)}, sample result: {results[0]}")

        self.logger.info(f"Saving results to {output_file}")
        self.save_results(results, output_file)
        self.logger.info(f"Classification completed. {len(results)} samples classified.")
        
        return results
    #end def run

if __name__ == "__main__":
    classifier = SampleSetClassifier()
    classifier.generate_training_set(
        input_file="data/sms_conversations.json",
        output_file="output/classified_results.jsonl"
    )