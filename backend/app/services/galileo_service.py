"""
Galileo service for logging negotiation traces and price optimization feedback.
Based on: https://v2docs.galileo.ai/getting-started/quickstart
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from contextlib import contextmanager
import os
import json

from ..core.config import settings
from ..core.models import NegotiationRun, NegotiationOutcome, SellerInventory, Offer, Message
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Galileo, but make it optional
try:
    from galileo import GalileoLogger
    from galileo.config import GalileoPythonConfig
    GALILEO_AVAILABLE = True
except ImportError:
    GALILEO_AVAILABLE = False
    logger.warning("Galileo SDK not installed. Install with: pip install galileo python-dotenv")


class GalileoFeedbackService:
    """Service for Galileo integration and price optimization feedback loop."""
    
    def __init__(self):
        self.initialized = False
        self.galileo_logger = None
        
        if not GALILEO_AVAILABLE:
            logger.warning("Galileo SDK not available - feedback service will be disabled")
            return
        
        if not settings.GALILEO_ENABLED:
            logger.info("Galileo is disabled in settings")
            return
        
        if not settings.GALILEO_API_KEY:
            logger.warning("GALILEO_API_KEY not set - Galileo service disabled")
            return
        
        try:
            # Set API key via environment variable (required by Galileo SDK)
            os.environ['GALILEO_API_KEY'] = settings.GALILEO_API_KEY
            
            # Initialize GalileoLogger with project and log stream
            # This is the correct API according to Galileo docs
            self.galileo_logger = GalileoLogger(
                project=settings.GALILEO_PROJECT,
                log_stream=settings.GALILEO_LOG_STREAM
            )
            self.initialized = True
            
            logger.info(f"✅ Galileo initialized: project={settings.GALILEO_PROJECT}, log_stream={settings.GALILEO_LOG_STREAM}")
            
            # Log project URLs
            try:
                config = GalileoPythonConfig.get()
                console_url = config.console_url or "https://app.galileo.ai"
                logger.info(f"🚀 GALILEO LOG INFORMATION:")
                logger.info(f"🔗 Console   : {console_url}")
                logger.info(f"📁 Project   : {settings.GALILEO_PROJECT}")
                logger.info(f"📝 Log Stream: {settings.GALILEO_LOG_STREAM}")
            except Exception as e:
                logger.debug(f"Could not get Galileo URLs: {e}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Galileo: {e}")
            self.initialized = False
    
    def is_enabled(self) -> bool:
        """Check if Galileo is enabled and initialized."""
        return self.initialized and self.galileo_logger is not None
    
    def start_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Start a Galileo session (non-blocking).
        Sessions group related traces for an entire interaction.
        
        Usage:
            galileo_service.start_session("session_123", {"buyer": "Alice"})
            # ... create traces ...
            galileo_service.end_session()
        """
        if not self.is_enabled():
            return
        
        try:
            # Convert metadata to strings (required by Galileo SDK)
            string_metadata = self._convert_metadata_to_strings(metadata)
            
            # Use async_start_session (the actual SDK method)
            import asyncio
            try:
                # Try to run in existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create task but don't wait
                    asyncio.create_task(self.galileo_logger.async_start_session(
                        session_name=session_id,
                        metadata=string_metadata
                    ))
                else:
                    # Run synchronously
                    loop.run_until_complete(self.galileo_logger.async_start_session(
                        session_name=session_id,
                        metadata=string_metadata
                    ))
            except RuntimeError:
                # No event loop, create one
                asyncio.run(self.galileo_logger.async_start_session(
                    session_name=session_id,
                    metadata=string_metadata
                ))
            
            logger.debug(f"Started Galileo session: {session_id}")
        except Exception as e:
            logger.warning(f"Error starting Galileo session: {e}")
    
    def end_session(self):
        """End the current Galileo session."""
        if not self.is_enabled():
            return
        
        try:
            if hasattr(self.galileo_logger, 'clear_session'):
                self.galileo_logger.clear_session()
                logger.debug("Ended Galileo session")
        except Exception as e:
            logger.debug(f"Error ending Galileo session: {e}")
    
    def _convert_metadata_to_strings(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Convert all metadata values to strings (required by Galileo SDK)."""
        if not metadata:
            return {}
        
        result = {}
        for key, value in metadata.items():
            if value is None:
                result[key] = ""
            elif isinstance(value, (list, dict)):
                result[key] = json.dumps(value)
            else:
                result[key] = str(value)
        return result
    
    def add_trace(self, name: str, input_text: str = "", output_text: str = "", metadata: Optional[Dict[str, Any]] = None):
        """
        Add a complete trace to Galileo.
        Traces represent complete AI interactions.
        
        Usage:
            trace_id = galileo_service.add_trace(
                name="negotiation_run_123",
                input_text="Negotiate for laptop",
                output_text="Deal at $950",
                metadata={"item": "laptop", "rounds": 3}
            )
        
        Returns:
            trace_id: UUID of the created trace
        """
        if not self.is_enabled():
            return None
        
        try:
            # Convert metadata to strings (required by Galileo SDK)
            string_metadata = self._convert_metadata_to_strings(metadata)
            
            # Use add_trace method (the actual SDK method)
            trace = self.galileo_logger.add_trace(
                name=name,
                input=input_text,
                output=output_text,
                user_metadata=string_metadata
            )
            logger.debug(f"Added Galileo trace: {name}")
            return trace.id if trace else None
        except Exception as e:
            logger.warning(f"Error adding Galileo trace: {e}")
            return None
    
    def add_span(self, name: str, input_text: str = "", output_text: str = "", metadata: Optional[Dict[str, Any]] = None, span_type: str = "agent"):
        """
        Add a span to the current trace.
        Spans represent distinct operations within a trace.
        
        Usage:
            galileo_service.add_span(
                name="buyer_message",
                input_text="What's your price?",
                metadata={"role": "buyer", "round": 1},
                span_type="agent"
            )
        
        Args:
            span_type: Type of span - "agent", "llm", "tool", "retriever", "workflow"
        
        Returns:
            span_id: UUID of the created span
        """
        if not self.is_enabled():
            return None
        
        try:
            # Convert metadata to strings (required by Galileo SDK)
            string_metadata = self._convert_metadata_to_strings(metadata)
            
            # Choose the appropriate span method based on type
            if span_type == "llm":
                span = self.galileo_logger.add_llm_span(
                    name=name,
                    input=input_text,
                    output=output_text,
                    user_metadata=string_metadata
                )
            elif span_type == "tool":
                span = self.galileo_logger.add_tool_span(
                    name=name,
                    input=input_text,
                    output=output_text,
                    user_metadata=string_metadata
                )
            elif span_type == "retriever":
                span = self.galileo_logger.add_retriever_span(
                    name=name,
                    input=input_text,
                    output=output_text,
                    user_metadata=string_metadata
                )
            elif span_type == "workflow":
                span = self.galileo_logger.add_workflow_span(
                    name=name,
                    input=input_text,
                    output=output_text,
                    user_metadata=string_metadata
                )
            else:  # agent (default)
                span = self.galileo_logger.add_agent_span(
                    name=name,
                    input=input_text,
                    output=output_text,
                    user_metadata=string_metadata
                )
            
            logger.debug(f"Added Galileo {span_type} span: {name}")
            return span.id if span else None
        except Exception as e:
            logger.warning(f"Error adding Galileo span: {e}")
            return None
    
    async def log_negotiation_trace(
        self,
        db: Session,
        run_id: str,
        session_id: str
    ):
        """
        Log a complete negotiation trace to Galileo.
        
        Creates a properly structured trace with:
        - Session: Groups all negotiations in this marketplace session
        - Trace: Represents one negotiation run for an item
        - Spans: Individual messages and rounds within the negotiation
        
        Based on: https://v2docs.galileo.ai/sdk-api/logging/logging-basics
        """
        if not self.is_enabled():
            return
        
        try:
            # Get negotiation run data
            run = db.query(NegotiationRun).filter(NegotiationRun.id == run_id).first()
            if not run:
                return
            
            from ..core.models import BuyerItem
            buyer_item = db.query(BuyerItem).filter(BuyerItem.id == run.buyer_item_id).first()
            if not buyer_item:
                return
            
            # Get outcome
            outcome = db.query(NegotiationOutcome).filter(
                NegotiationOutcome.negotiation_run_id == run_id
            ).first()
            
            # Get all messages in order
            messages = db.query(Message).filter(
                Message.negotiation_run_id == run_id
            ).order_by(Message.turn_number).all()
            
            # Get all offers
            offers = db.query(Offer).join(Message).filter(
                Message.negotiation_run_id == run_id
            ).all()
            offer_map = {offer.message_id: offer for offer in offers}
            
            # Start a session for this marketplace session (groups related negotiations)
            self.start_session(f"session_{session_id}", {"session_id": session_id})
            
            # Create trace input (the buyer's initial request)
            trace_input = f"Negotiate for {buyer_item.item_name} (qty: {buyer_item.quantity_needed}, budget: ${buyer_item.min_price_per_unit}-${buyer_item.max_price_per_unit})"
            
            # Create trace metadata
            trace_metadata = {
                "run_id": run_id,
                "session_id": session_id,
                "item_name": buyer_item.item_name,
                "quantity_needed": buyer_item.quantity_needed,
                "buyer_min_price": buyer_item.min_price_per_unit,
                "buyer_max_price": buyer_item.max_price_per_unit,
                "rounds": run.current_round,
                "status": run.status,
            }
            
            # Add outcome data if available
            trace_output = ""
            if outcome:
                trace_metadata.update({
                    "final_price": outcome.final_price_per_unit,
                    "decision_type": outcome.decision_type,
                    "selected_seller_id": outcome.selected_seller_id,
                    "total_cost": outcome.total_cost
                })
                
                if outcome.decision_type == 'deal':
                    trace_output = f"Deal: ${outcome.final_price_per_unit}/unit with seller {outcome.selected_seller_id} (total: ${outcome.total_cost})"
                else:
                    trace_output = f"No deal: {outcome.decision_reason[:100]}" if outcome.decision_reason else "No deal"
            
            # Add the trace
            trace_id = self.add_trace(
                name=f"negotiate_{buyer_item.item_name}",
                input_text=trace_input,
                output_text=trace_output,
                metadata=trace_metadata
            )
            
            # Log each message as a span
            for msg in messages:
                # Log buyer message
                if msg.sender_type == "buyer":
                    # Parse mentioned_agents from JSON text field
                    mentioned_agents = []
                    if msg.mentioned_agents:
                        try:
                            mentioned_agents = json.loads(msg.mentioned_agents)
                        except (json.JSONDecodeError, TypeError):
                            mentioned_agents = []
                    
                    # Add buyer span
                    self.add_span(
                        name=f"round_{msg.turn_number}_buyer",
                        input_text=msg.message_text[:500] if msg.message_text else "",
                        metadata={
                            "round": msg.turn_number,
                            "sender_type": "buyer",
                            "sender_name": msg.sender_name,
                            "mentioned_sellers": mentioned_agents
                        },
                        span_type="agent"
                    )
                
                # Log seller response
                elif msg.sender_type == "seller":
                    offer = offer_map.get(msg.id)
                    
                    # Build output with offer details
                    span_output = ""
                    if offer:
                        span_output = f"Offer: ${offer.price_per_unit}/unit (qty: {offer.quantity})"
                    
                    # Add seller span
                    self.add_span(
                        name=f"round_{msg.turn_number}_seller_{msg.sender_name}",
                        input_text=msg.message_text[:500] if msg.message_text else "",
                        output_text=span_output,
                        metadata={
                            "round": msg.turn_number,
                            "sender_type": "seller",
                            "sender_name": msg.sender_name,
                            "offer_price": offer.price_per_unit if offer else None,
                            "offer_quantity": offer.quantity if offer else None
                        },
                        span_type="agent"
                    )
            
            # Flush the logger to ensure data is sent to Galileo
            if hasattr(self.galileo_logger, 'flush'):
                self.galileo_logger.flush()
            
            logger.info(f"[OK] Logged negotiation trace to Galileo: {buyer_item.item_name} (run: {run_id})")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to log negotiation trace to Galileo: {e}", exc_info=True)
    
    
    async def analyze_price_optimization(
        self,
        db: Session,
        session_id: str,
        ai_summary: Dict
    ) -> Dict[str, float]:
        """
        Analyze negotiation outcomes and suggest least_price adjustments.
        
        Uses Galileo to track price optimization experiments.
        
        Returns:
            Dict mapping (seller_id_item_id) -> suggested_new_least_price
        """
        if not self.is_enabled():
            return {}
        
        try:
            # Get all completed negotiations for this session
            outcomes = db.query(NegotiationOutcome).join(
                NegotiationRun
            ).filter(
                NegotiationRun.session_id == session_id,
                NegotiationOutcome.decision_type == 'deal'
            ).all()
            
            price_adjustments = {}
            adjustments_made = 0
            adjustment_details = []  # Collect details for the trace output
            
            # Start session for price optimization
            self.start_session(f"session_{session_id}", {"session_id": session_id})
            
            # Create trace for price optimization analysis FIRST
            trace_input = f"Price optimization analysis for session {session_id} ({len(outcomes)} completed deals)"
            trace_metadata = {
                "session_id": session_id,
                "outcomes_count": len(outcomes),
                "analysis_type": "price_optimization"
            }
            
            # Add the trace BEFORE adding spans
            trace_id = self.add_trace(
                name="price_optimization_analysis",
                input_text=trace_input,
                output_text="",  # Will update after analysis
                metadata=trace_metadata
            )
            
            logger.info(f"[GALILEO] Started price optimization trace: {trace_id}")
            
            # Analyze each outcome
            for outcome in outcomes:
                run = outcome.negotiation_run
                
                # Get all sellers that participated
                from ..core.models import NegotiationParticipant, BuyerItem
                participants = db.query(NegotiationParticipant).filter(
                    NegotiationParticipant.negotiation_run_id == run.id
                ).all()
                
                buyer_item = db.query(BuyerItem).filter(
                    BuyerItem.id == run.buyer_item_id
                ).first()
                
                if not buyer_item:
                    continue
                
                # Analyze each participating seller
                for participant in participants:
                    seller_id = participant.seller_id
                    
                    # Get seller's inventory
                    inventory = db.query(SellerInventory).filter(
                        SellerInventory.seller_id == seller_id,
                        SellerInventory.item_name == buyer_item.item_name
                    ).first()
                    
                    if not inventory:
                        continue
                    
                    # Get seller's offers
                    seller_offers = db.query(Offer).join(Message).filter(
                        Message.negotiation_run_id == run.id,
                        Offer.seller_id == seller_id
                    ).order_by(Offer.price_per_unit).all()
                    
                    if not seller_offers:
                        continue
                    
                    # Analyze pricing
                    won_deal = (outcome.selected_seller_id == seller_id)
                    final_offer_price = seller_offers[-1].price_per_unit if seller_offers else None
                    
                    # Suggest adjustment
                    adjustment = self._suggest_price_adjustment(
                        seller_id=seller_id,
                        item_name=buyer_item.item_name,
                        current_least_price=inventory.least_price,
                        final_deal_price=outcome.final_price_per_unit,
                        won_deal=won_deal,
                        seller_final_offer=final_offer_price,
                        buyer_max_price=buyer_item.max_price_per_unit,
                        ai_summary=ai_summary
                    )
                    
                    if adjustment:
                        key = f"{seller_id}_{buyer_item.item_id}"
                        price_adjustments[key] = adjustment
                        adjustments_made += 1
                        
                        # Collect details for output
                        reduction_pct = round(((inventory.least_price - adjustment) / inventory.least_price) * 100, 2)
                        adjustment_details.append(f"{buyer_item.item_name}: ${inventory.least_price:.2f} -> ${adjustment:.2f} (-{reduction_pct}%)")
                        
                        # Log each adjustment as a span
                        span_id = self.add_span(
                            name=f"adjust_{seller_id[:8]}_{buyer_item.item_name}",
                            input_text=f"Analyze {seller_id[:8]}... pricing for {buyer_item.item_name}",
                            output_text=f"Suggested: ${inventory.least_price:.2f} -> ${adjustment:.2f} (-{reduction_pct}%)",
                            metadata={
                                "seller_id": seller_id,
                                "item_name": buyer_item.item_name,
                                "current_least_price": inventory.least_price,
                                "suggested_least_price": adjustment,
                                "reduction_pct": reduction_pct,
                                "won_deal": str(won_deal),
                                "final_deal_price": outcome.final_price_per_unit
                            },
                            span_type="workflow"
                        )
                        logger.debug(f"[GALILEO] Added adjustment span: {span_id}")
            
            # Conclude the first trace (required by Galileo SDK before adding another trace)
            if hasattr(self.galileo_logger, 'conclude'):
                self.galileo_logger.conclude()
                logger.debug("[GALILEO] Concluded first trace")
            
            # Create a summary trace with complete output
            if adjustments_made > 0:
                trace_output = f"Suggested {adjustments_made} price adjustments:\n" + "\n".join(adjustment_details)
            else:
                trace_output = "No price adjustments needed - all prices are optimal"
            
            # Add final summary trace with all details
            summary_trace_id = self.add_trace(
                name="price_optimization_summary",
                input_text=f"Session {session_id}: Analyzed {len(outcomes)} negotiations",
                output_text=trace_output,
                metadata={
                    "session_id": session_id,
                    "adjustments_made": adjustments_made,
                    "deals_analyzed": len(outcomes),
                    "has_adjustments": str(adjustments_made > 0)
                }
            )
            
            logger.info(f"[GALILEO] Price optimization summary trace: {summary_trace_id}")
            logger.info(f"[GALILEO] Complete: {adjustments_made} adjustments")
            
            # Flush the logger to ensure all data is sent
            if hasattr(self.galileo_logger, 'flush'):
                self.galileo_logger.flush()
                logger.debug("[GALILEO] Logger flushed")
            
            logger.info(f"[OK] Price optimization analysis logged: {adjustments_made} adjustments")
            
            return price_adjustments
            
        except Exception as e:
            logger.error(f"[ERROR] Price optimization analysis failed: {e}", exc_info=True)
            return {}
    
    def _suggest_price_adjustment(
        self,
        seller_id: str,
        item_name: str,
        current_least_price: float,
        final_deal_price: float,
        won_deal: bool,
        seller_final_offer: Optional[float],
        buyer_max_price: float,
        ai_summary: Dict
    ) -> Optional[float]:
        """
        Suggest a new least_price based on negotiation outcomes.
        
        Conservative approach: max 10% reduction per iteration.
        """
        max_reduction_pct = 0.10
        
        if won_deal:
            # Seller won - they were competitive
            if seller_final_offer and seller_final_offer <= current_least_price * 1.05:
                # Sold very close to floor - could lower by 2-5%
                suggested = current_least_price * 0.97  # 3% reduction
            else:
                return None
        else:
            # Seller lost - analyze why
            if final_deal_price < current_least_price:
                # Winner was more competitive
                suggested = min(
                    final_deal_price * 1.02,  # 2% above winner
                    current_least_price * (1 - max_reduction_pct)  # Max 10% reduction
                )
            else:
                # Small reduction to be more competitive
                suggested = current_least_price * 0.98  # 2% reduction
        
        # Safety: never go below 90% of current
        return max(suggested, current_least_price * 0.90)


# Singleton instance
galileo_feedback_service = GalileoFeedbackService()

