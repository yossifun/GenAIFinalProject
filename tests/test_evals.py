"""
Model Evaluation Script for GenAI SMS Chatbot

This script evaluates the performance of the multi-agent chatbot system
using labeled conversation data and generates performance metrics.
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import List, Dict, Any

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import ChatbotSystem

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


def load_test_data(file_path: str) -> List[Dict[str, Any]]:
    """Load test data from JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} test conversations")
        return data
    except FileNotFoundError:
        print(f"❌ Test data file not found: {file_path}")
        print("Creating sample test data...")
        return create_sample_test_data()
    except Exception as e:
        print(f"❌ Error loading test data: {str(e)}")
        return []


def create_sample_test_data() -> List[Dict[str, Any]]:
    """Create sample test data for demonstration."""
    sample_data = [
        {
            "id": "conv_001",
            "turns": [
                {
                    "user_message": "Hi, I'm interested in the Python developer position",
                    "bot_response": "Great! I'd love to tell you more about the role. What's your background in Python development?",
                    "correct_action": "continue"
                },
                {
                    "user_message": "I have 5 years of experience with Django and Flask",
                    "bot_response": "Excellent! That's exactly what we're looking for. Would you like to schedule an interview?",
                    "correct_action": "schedule"
                }
            ]
        },
        {
            "id": "conv_002",
            "turns": [
                {
                    "user_message": "I'm not interested in this position",
                    "bot_response": "Thank you for your time. Good luck with your job search!",
                    "correct_action": "end"
                }
            ]
        },
        {
            "id": "conv_003",
            "turns": [
                {
                    "user_message": "What are the job requirements?",
                    "bot_response": "Here are the key requirements for our Python Developer position...",
                    "correct_action": "continue"
                },
                {
                    "user_message": "I'd like to schedule an interview",
                    "bot_response": "Great! I have several interview slots available...",
                    "correct_action": "schedule"
                }
            ]
        }
    ]
    
    print(f"✅ Created {len(sample_data)} sample test conversations")
    return sample_data


def evaluate_conversation(chatbot: ChatbotSystem, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluate a single conversation."""
    results = []
    
    # Reset conversation for each test
    chatbot.reset_conversation()
    
    for turn in conversation.get('turns', []):
        user_message = turn.get('user_message', '')
        correct_action = turn.get('correct_action', 'continue')
        
        if user_message:
            # Process with chatbot
            response = chatbot.process_message(user_message)
            predicted_action = response['action']
            
            # Record result
            result = {
                'conversation_id': conversation.get('id', 'unknown'),
                'user_message': user_message,
                'correct_action': correct_action,
                'predicted_action': predicted_action,
                'is_correct': correct_action == predicted_action,
                'bot_response': response['message']
            }
            results.append(result)
    
    return results


def run_evaluation(chatbot: ChatbotSystem, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run evaluation on all test conversations."""
    all_results = []
    
    print("🔄 Running evaluation...")
    
    for i, conversation in enumerate(test_data):
        print(f"  Processing conversation {i+1}/{len(test_data)}: {conversation.get('id', 'unknown')}")
        results = evaluate_conversation(chatbot, conversation)
        all_results.extend(results)
    
    print(f"✅ Evaluation complete. {len(all_results)} total predictions evaluated.")
    return all_results


def calculate_metrics(results_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate performance metrics."""
    
    # Overall accuracy
    overall_accuracy = results_df['is_correct'].mean()
    
    # Accuracy by action type
    accuracy_by_action = results_df.groupby('correct_action')['is_correct'].mean()
    
    # Confusion matrix
    confusion_matrix = pd.crosstab(
        results_df['correct_action'], 
        results_df['predicted_action'], 
        margins=True
    )
    
    # Action distribution
    action_distribution = results_df['correct_action'].value_counts()
    
    # Error analysis
    errors = results_df[~results_df['is_correct']]
    error_patterns = errors.groupby(['correct_action', 'predicted_action']).size()
    
    return {
        'overall_accuracy': overall_accuracy,
        'accuracy_by_action': accuracy_by_action,
        'confusion_matrix': confusion_matrix,
        'action_distribution': action_distribution,
        'error_patterns': error_patterns,
        'total_predictions': len(results_df),
        'total_errors': len(errors)
    }


def create_visualizations(metrics: Dict[str, Any], save_path: str = None):
    """Create and save performance visualizations."""
    
    # Create visualizations
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('GenAI SMS Chatbot - Performance Analysis', fontsize=16, fontweight='bold')
    
    # 1. Overall Accuracy
    axes[0, 0].pie([metrics['overall_accuracy'], 1-metrics['overall_accuracy']], 
                   labels=['Correct', 'Incorrect'], 
                   autopct='%1.1f%%', 
                   colors=['lightgreen', 'lightcoral'])
    axes[0, 0].set_title('Overall Accuracy')
    
    # 2. Accuracy by Action
    actions = list(metrics['accuracy_by_action'].index)
    accuracies = list(metrics['accuracy_by_action'].values)
    bars = axes[0, 1].bar(actions, accuracies, color=['skyblue', 'lightgreen', 'orange'])
    axes[0, 1].set_title('Accuracy by Action Type')
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].set_ylim(0, 1)
    
    # Add value labels on bars
    for bar, acc in zip(bars, accuracies):
        axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                        f'{acc:.1%}', ha='center', va='bottom')
    
    # 3. Action Distribution
    action_counts = metrics['action_distribution']
    axes[1, 0].pie(action_counts.values, labels=action_counts.index, autopct='%1.1f%%')
    axes[1, 0].set_title('Distribution of Correct Actions')
    
    # 4. Confusion Matrix Heatmap
    conf_matrix = metrics['confusion_matrix'].iloc[:-1, :-1]  # Remove margins
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', ax=axes[1, 1])
    axes[1, 1].set_title('Confusion Matrix')
    axes[1, 1].set_xlabel('Predicted Action')
    axes[1, 1].set_ylabel('Correct Action')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Visualizations saved to {save_path}")
    else:
        plt.show()


def save_evaluation_results(results_df: pd.DataFrame, metrics: Dict[str, Any], output_dir: str = "evaluation_results"):
    """Save evaluation results to files."""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed results
    results_file = os.path.join(output_dir, f"evaluation_results_{timestamp}_detailed.csv")
    results_df.to_csv(results_file, index=False)
    
    # Save metrics summary
    summary = {
        'overall_accuracy': float(metrics['overall_accuracy']),
        'total_predictions': metrics['total_predictions'],
        'total_errors': metrics['total_errors'],
        'accuracy_by_action': metrics['accuracy_by_action'].to_dict(),
        'action_distribution': metrics['action_distribution'].to_dict(),
        'evaluation_date': datetime.now().isoformat()
    }
    
    summary_file = os.path.join(output_dir, f"evaluation_results_{timestamp}_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Save confusion matrix
    conf_matrix_file = os.path.join(output_dir, f"confusion_matrix_{timestamp}.csv")
    metrics['confusion_matrix'].to_csv(conf_matrix_file)
    
    # Create visualizations
    viz_file = os.path.join(output_dir, f"performance_analysis_{timestamp}.png")
    create_visualizations(metrics, viz_file)
    
    print(f"✅ Results saved to {output_dir}/")
    print(f"  - Detailed results: {results_file}")
    print(f"  - Summary: {summary_file}")
    print(f"  - Confusion matrix: {conf_matrix_file}")
    print(f"  - Visualizations: {viz_file}")


def print_summary_and_recommendations(metrics: Dict[str, Any], test_data: List[Dict[str, Any]]):
    """Print evaluation summary and recommendations."""
    
    print("\n" + "="*60)
    print("📋 EVALUATION SUMMARY")
    print("="*60)
    print(f"Model Performance: {metrics['overall_accuracy']:.1%} accuracy")
    print(f"Test Coverage: {metrics['total_predictions']} predictions across {len(test_data)} conversations")
    print(f"Error Rate: {metrics['total_errors']} errors ({1-metrics['overall_accuracy']:.1%})")
    
    print("\n🎯 RECOMMENDATIONS")
    print("="*60)
    
    if metrics['overall_accuracy'] >= 0.9:
        print("✅ Excellent performance! The model is ready for production.")
    elif metrics['overall_accuracy'] >= 0.8:
        print("✅ Good performance. Consider fine-tuning for specific edge cases.")
    elif metrics['overall_accuracy'] >= 0.7:
        print("⚠️  Moderate performance. Fine-tuning recommended.")
    else:
        print("❌ Poor performance. Significant improvements needed.")
    
    # Action-specific recommendations
    print("\nAction-Specific Recommendations:")
    for action, accuracy in metrics['accuracy_by_action'].items():
        if accuracy < 0.8:
            print(f"  • {action.title()} actions need improvement (accuracy: {accuracy:.1%})")
        else:
            print(f"  • {action.title()} actions performing well (accuracy: {accuracy:.1%})")
    
    print("\n🔧 NEXT STEPS")
    print("="*60)
    print("1. Review error patterns and improve prompts")
    print("2. Collect more training data for low-performing actions")
    print("3. Consider fine-tuning the Exit Advisor agent")
    print("4. Implement additional validation rules")
    print("5. Deploy to production with monitoring")


def main():
    """Main evaluation function."""
    
    print("🤖 GenAI SMS Chatbot - Model Evaluation")
    print("="*60)
    
    # Load test data
    test_data = load_test_data("../data/sms_conversations.json")
    print(f"📊 Total test conversations: {len(test_data)}")
    
    if not test_data:
        print("❌ No test data available. Exiting.")
        return
    
    # Initialize chatbot system
    print("\n🔧 Initializing chatbot system...")
    chatbot = ChatbotSystem()
    print("✅ Chatbot system initialized")
    
    # Run evaluation
    print("\n🔄 Starting evaluation...")
    evaluation_results = run_evaluation(chatbot, test_data)
    
    if not evaluation_results:
        print("❌ No evaluation results. Exiting.")
        return
    
    # Convert to DataFrame for analysis
    df_results = pd.DataFrame(evaluation_results)
    print(f"\n📋 Results DataFrame shape: {df_results.shape}")
    
    # Calculate metrics
    print("\n📊 Calculating performance metrics...")
    metrics = calculate_metrics(df_results)
    
    # Print metrics
    print("\n📊 PERFORMANCE METRICS")
    print("="*50)
    print(f"Overall Accuracy: {metrics['overall_accuracy']:.2%}")
    print(f"Total Predictions: {metrics['total_predictions']}")
    print(f"Total Errors: {metrics['total_errors']}")
    print(f"\nAccuracy by Action:")
    for action, accuracy in metrics['accuracy_by_action'].items():
        print(f"  {action}: {accuracy:.2%}")
    
    # Save results
    print("\n💾 Saving results...")
    save_evaluation_results(df_results, metrics)
    
    # Print summary and recommendations
    print_summary_and_recommendations(metrics, test_data)
    
    print("\n🎉 Evaluation complete!")


if __name__ == "__main__":
    main() 