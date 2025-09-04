"""
Fine-tuning module for the GenAI SMS Chatbot.

This module handles the fine-tuning of the Exit Advisor agent to improve
its ability to detect conversation scenarios that should end.
"""

import json
import logging
import os
from typing import List, Dict, Any
from datetime import datetime
from sklearn.model_selection import train_test_split

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from config.project_config import BaseConfigurable


class FineTuningManager(BaseConfigurable):
    """
    Manages the fine-tuning process for the Exit Advisor agent.
    """
    
    def __init__(self):
        super().__init__()

        """Initialize the fine-tuning manager."""
        self.llm = ChatOpenAI(
            model=os.getenv('FINE_TUNING_MODEL', 'gpt-3.5-turbo'),
            temperature=0.1
        )
        
    def prepare_training_data(self, conversations_file: str) -> List[Dict[str, Any]]:
        """
        Prepare training data from labeled conversations.
        
        Args:
            conversations_file: Path to the conversations JSON file
            
        Returns:
            List of training examples
        """
        try:
            with open(conversations_file, 'r') as f:
                conversations = json.load(f)
            
            training_data = []
            
            for conversation in conversations:
                # Extract labeled actions from conversation
                for turn in conversation.get('turns', []):
                    if 'user_message' in turn and 'correct_action' in turn:
                        training_example = {
                            'user_message': turn['user_message'],
                            'context': self._extract_context(conversation, turn),
                            'correct_action': turn['correct_action'],
                            'conversation_id': conversation.get('id', 'unknown')
                        }
                        training_data.append(training_example)
            
            self.logger.info(f"Prepared {len(training_data)} training examples")
            return training_data
            
        except Exception as e:
            self.logger.error(f"Error preparing training data: {str(e)}")
            return []
    
    def _extract_context(self, conversation: Dict[str, Any], current_turn: Dict[str, Any]) -> str:
        """
        Extract conversation context up to the current turn.
        
        Args:
            conversation: Full conversation data
            current_turn: Current turn being processed
            
        Returns:
            Context string
        """
        context_parts = []
        turns = conversation.get('turns', [])
        
        # Find the index of the current turn
        current_index = None
        for i, turn in enumerate(turns):
            if turn == current_turn:
                current_index = i
                break
        
        if current_index is None:
            return ""
        
        # Get previous turns for context (up to 3 exchanges)
        start_index = max(0, current_index - 6)
        for i in range(start_index, current_index):
            turn = turns[i]
            if 'user_message' in turn:
                context_parts.append(f"User: {turn['user_message']}")
            if 'bot_response' in turn:
                context_parts.append(f"Bot: {turn['bot_response']}")
        
        return "\n".join(context_parts)
    
    def create_fine_tuning_dataset(self, training_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create a dataset suitable for fine-tuning.
        
        Args:
            training_data: List of training examples
            
        Returns:
            List of fine-tuning examples
        """
        fine_tuning_data = []
        
        for example in training_data:
            # Create system message
            system_message = """You are an exit advisor for a job candidate chatbot system. Your role is to determine if it's appropriate to end the conversation with a candidate.

You should recommend ending the conversation if:
1. The candidate explicitly states they are not interested
2. The candidate already has a job and is not looking
3. The candidate asks to stop the conversation
4. The candidate is not qualified for the position
5. The candidate is rude or inappropriate
6. The candidate is clearly a bot or spam

You should NOT recommend ending if:
1. The candidate is asking questions about the position
2. The candidate is providing information about their background
3. The candidate shows interest but needs more information
4. The candidate is negotiating or discussing terms
5. The candidate is asking about the interview process

Respond with ONLY "yes" or "no"."""
            
            # Create user message
            if example['context']:
                user_message = f"Context:\n{example['context']}\n\nCurrent message: {example['user_message']}\n\nShould the conversation end?"
            else:
                user_message = f"Current message: {example['user_message']}\n\nShould the conversation end?"
            
            # Determine expected response
            expected_response = "yes" if example['correct_action'] == 'end' else "no"
            
            fine_tuning_example = {
                'messages': [
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': user_message},
                    {'role': 'assistant', 'content': expected_response}
                ]
            }
            
            fine_tuning_data.append(fine_tuning_example)
        
        return fine_tuning_data
    
    def evaluate_model_performance(self, test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate the model's performance on test data.
        
        Args:
            test_data: List of test examples
            
        Returns:
            Dictionary with evaluation metrics
        """
        correct_predictions = 0
        total_predictions = len(test_data)
        
        predictions = []
        actual_labels = []
        
        for example in test_data:
            try:
                # Get model prediction
                messages = [
                    SystemMessage(content=example['messages'][0]['content']),
                    HumanMessage(content=example['messages'][1]['content'])
                ]
                
                response = self.llm.invoke(messages)
                prediction = response.content.strip().lower()
                
                # Get actual label
                actual = example['messages'][2]['content'].strip().lower()
                
                # Check if prediction is correct
                if prediction == actual:
                    correct_predictions += 1
                
                predictions.append(prediction)
                actual_labels.append(actual)
                
            except Exception as e:
                self.logger.error(f"Error evaluating example: {str(e)}")
                continue
        
        # Calculate metrics
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        # Calculate confusion matrix
        confusion_matrix = self._calculate_confusion_matrix(predictions, actual_labels)
        
        return {
            'accuracy': accuracy,
            'total_predictions': total_predictions,
            'correct_predictions': correct_predictions,
            'confusion_matrix': confusion_matrix
        }
    
    def _calculate_confusion_matrix(self, predictions: List[str], actuals: List[str]) -> Dict[str, int]:
        """
        Calculate confusion matrix for binary classification.
        
        Args:
            predictions: List of predicted labels
            actuals: List of actual labels
            
        Returns:
            Dictionary with confusion matrix values
        """
        tp = fp = tn = fn = 0
        
        for pred, actual in zip(predictions, actuals):
            if pred == 'yes' and actual == 'yes':
                tp += 1
            elif pred == 'yes' and actual == 'no':
                fp += 1
            elif pred == 'no' and actual == 'no':
                tn += 1
            elif pred == 'no' and actual == 'yes':
                fn += 1
        
        return {
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn
        }
    
    def save_evaluation_results(self, results: Dict[str, Any], output_file: str):
        """
        Save evaluation results to a file.
        
        Args:
            results: Evaluation results
            output_file: Path to output file
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            self.logger.info(f"Evaluation results saved to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving evaluation results: {str(e)}")
    
    def run_fine_tuning_pipeline(self, conversations_file: str, output_dir: str = "fine_tuning_results"):
        """
        Run the complete fine-tuning pipeline.
        
        Args:
            conversations_file: Path to conversations file
            output_dir: Directory to save results
        """
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Prepare training data
            self.logger.info("Preparing training data...")
            training_data = self.prepare_training_data(conversations_file)
            
            if not training_data:
                self.logger.error("No training data found")
                return
            
            # Split into train and test sets
            train_data, test_data = train_test_split(
                training_data, 
                test_size=0.2, 
                random_state=42
            )
            
            self.logger.info(f"Training set size: {len(train_data)}")
            self.logger.info(f"Test set size: {len(test_data)}")
            
            # Create fine-tuning dataset
            self.logger.info("Creating fine-tuning dataset...")
            fine_tuning_data = self.create_fine_tuning_dataset(train_data)
            
            # Save fine-tuning dataset
            dataset_file = os.path.join(output_dir, "fine_tuning_dataset.jsonl")
            with open(dataset_file, 'w') as f:
                for example in fine_tuning_data:
                    f.write(json.dumps(example) + '\n')
            
            self.logger.info(f"Fine-tuning dataset saved to {dataset_file}")
            
            # Evaluate current model performance
            self.logger.info("Evaluating model performance...")
            evaluation_results = self.evaluate_model_performance(test_data)
            
            # Save evaluation results
            results_file = os.path.join(output_dir, "evaluation_results.json")
            self.save_evaluation_results(evaluation_results, results_file)
            
            # Print summary
            print("\n" + "="*50)
            print("FINE-TUNING PIPELINE RESULTS")
            print("="*50)
            print(f"Training examples: {len(train_data)}")
            print(f"Test examples: {len(test_data)}")
            print(f"Model accuracy: {evaluation_results['accuracy']:.2%}")
            print(f"Confusion Matrix:")
            cm = evaluation_results['confusion_matrix']
            print(f"  True Positives: {cm['true_positives']}")
            print(f"  False Positives: {cm['false_positives']}")
            print(f"  True Negatives: {cm['true_negatives']}")
            print(f"  False Negatives: {cm['false_negatives']}")
            print(f"\nResults saved to: {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Error in fine-tuning pipeline: {str(e)}")


def main():
    """Main function for running fine-tuning."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run fine-tuning for Exit Advisor")
    parser.add_argument("--conversations", required=True, help="Path to conversations JSON file")
    parser.add_argument("--output", default="fine_tuning_results", help="Output directory")
    
    args = parser.parse_args()
    
    # Initialize fine-tuning manager
    ft_manager = FineTuningManager()
    
    # Run pipeline
    ft_manager.run_fine_tuning_pipeline(args.conversations, args.output)


if __name__ == "__main__":
    main() 