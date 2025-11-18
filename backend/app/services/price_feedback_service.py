"""
Price feedback service - applies Galileo insights to improve seller pricing.
"""

from typing import Dict
from sqlalchemy.orm import Session
from ..core.models import SellerInventory
from ..utils.logger import get_logger
from .galileo_service import galileo_feedback_service

logger = get_logger(__name__)


class PriceFeedbackService:
    """Service for applying price feedback from negotiation outcomes."""
    
    async def apply_feedback_after_summary(
        self,
        db: Session,
        session_id: str,
        ai_summaries: Dict[str, Dict]
    ) -> Dict:
        """
        Apply feedback loop after AI summaries are generated.
        
        Args:
            db: Database session
            session_id: Session ID
            ai_summaries: Dict mapping run_id -> AI summary data
        
        Returns:
            Dict with adjustment results
        """
        try:
            # Get overall session summary for context
            overall_summary = ai_summaries.get("overall", {})
            
            # Analyze price optimization opportunities using Galileo
            price_adjustments = await galileo_feedback_service.analyze_price_optimization(
                db=db,
                session_id=session_id,
                ai_summary=overall_summary
            )
            
            # Apply adjustments
            applied_adjustments = []
            for key, new_least_price in price_adjustments.items():
                seller_id, item_id = key.split("_", 1)
                
                # Get inventory item
                inventory = db.query(SellerInventory).filter(
                    SellerInventory.seller_id == seller_id,
                    SellerInventory.item_id == item_id
                ).first()
                
                if not inventory:
                    continue
                
                # Validate constraints
                if new_least_price <= inventory.cost_price:
                    logger.warning(
                        f"Cannot lower {inventory.item_name} for seller {seller_id}: "
                        f"new price {new_least_price} <= cost_price {inventory.cost_price}"
                    )
                    continue
                
                if new_least_price >= inventory.selling_price:
                    logger.warning(
                        f"Cannot raise {inventory.item_name} for seller {seller_id}: "
                        f"new price {new_least_price} >= selling_price {inventory.selling_price}"
                    )
                    continue
                
                # Apply adjustment
                old_price = inventory.least_price
                inventory.least_price = new_least_price
                db.commit()
                
                applied_adjustments.append({
                    "seller_id": seller_id,
                    "item_name": inventory.item_name,
                    "old_least_price": old_price,
                    "new_least_price": new_least_price,
                    "reduction_pct": ((old_price - new_least_price) / old_price) * 100
                })
                
                logger.info(
                    f"✅ Adjusted least_price for {inventory.item_name} (seller {seller_id}): "
                    f"${old_price:.2f} → ${new_least_price:.2f} "
                    f"({applied_adjustments[-1]['reduction_pct']:.1f}% reduction)"
                )
            
            return {
                "session_id": session_id,
                "adjustments_applied": len(applied_adjustments),
                "adjustments": applied_adjustments
            }
            
        except Exception as e:
            logger.error(f"Error applying price feedback: {e}")
            db.rollback()
            return {
                "session_id": session_id,
                "adjustments_applied": 0,
                "error": str(e)
            }


# Singleton instance
price_feedback_service = PriceFeedbackService()

