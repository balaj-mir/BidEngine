import os
import sys
import logging

# Add backend to python path to import service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ml_win_scorer import MLWinScorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_scorer")

def main():
    bid_history_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "bid_history.json")
    if not os.path.exists(bid_history_path):
        logger.error(f"Bid history dataset does not exist: {bid_history_path}")
        return

    logger.info("Initializing ML Win Scorer training...")
    scorer = MLWinScorer()
    
    try:
        metrics = scorer.train(bid_history_path)
        logger.info("Training complete!")
        print("\n" + "="*40)
        print("ML Win Scorer Calibration Metrics:")
        print(f"Accuracy: {metrics['accuracy']:.4f}")
        print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
        print(f"Cross-Validation AUC Mean: {metrics['cv_auc_mean']:.4f}")
        print(f"Training set count: {metrics['n_train']}")
        print(f"Testing set count: {metrics['n_test']}")
        print("\nFeature Importances:")
        for feat, val in sorted(metrics['feature_importance'].items(), key=lambda x: x[1], reverse=True):
            print(f" - {feat}: {val:.4f}")
        print("="*40 + "\n")
    except Exception as e:
        logger.exception(f"Failed to train win scorer model: {e}")

if __name__ == "__main__":
    main()
