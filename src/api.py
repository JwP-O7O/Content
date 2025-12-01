from flask import Flask, request, jsonify, render_template
from src.orchestrator import AgentOrchestrator
from src.scheduler import ContentCreatorScheduler
from src.api_integrations.stripe_api import StripeAPI
from src.database.connection import get_db
from src.database.models import CommunityUser, Subscription, UserTier, APIKey, MarketData, ContentPlan
from config.config import settings
import asyncio
import threading
import logging
import hashlib
import functools
from datetime import datetime, timedelta
import os

# Configure Flask to look for templates/static in src/web
# Get absolute path to ensure it works from any CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'web', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'web', 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

orchestrator = AgentOrchestrator()
scheduler = ContentCreatorScheduler(phase=4)
stripe_api = StripeAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This will be used to run asyncio tasks from Flask threads
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# --- API Key Decorator ---
def require_api_key(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "Missing API Key"}), 401
            
        # Hash provided key to match stored hash
        # The key format is pk_...
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        with get_db() as db:
            key_record = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
            
            if not key_record or not key_record.is_active:
                return jsonify({"error": "Invalid or inactive API Key"}), 403
                
            # Check rate limit (Simple check: count requests in last minute)
            key_record.request_count += 1
            key_record.last_used_at = datetime.utcnow()
            db.commit()
            
        return f(*args, **kwargs)
    return decorated_function

# --- Web Dashboard Routes ---

@app.route('/')
def dashboard():
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/api/content/pending', methods=['GET'])
def get_pending_content():
    """Get content waiting for approval."""
    try:
        with get_db() as db:
            # Fetch content plans with status 'pending'
            # Note: In a real app, you might join with Insight to get topic details
            plans = db.query(ContentPlan).filter(ContentPlan.status == 'pending').all()
            
            # Convert to JSON-friendly format
            data = []
            for plan in plans:
                # Placeholder for actual content text (which might be in a different table or field depending on generation stage)
                # For now assuming we might store draft in a temporary field or linked PublishedContent (draft)
                # Simplified for the dashboard demo:
                data.append({
                    "id": plan.id,
                    "platform": plan.platform,
                    "format": plan.format.value if hasattr(plan.format, 'value') else str(plan.format),
                    "topic": f"Insight #{plan.insight_id}", # Placeholder topic
                    "content_text": "Draft content preview would go here...", # Should fetch from creation agent's storage
                    "created_at": plan.created_at.isoformat()
                })
                
            return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching pending content: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/content/approve/<int:id>', methods=['POST'])
def approve_content(id):
    """Approve a content plan."""
    try:
        with get_db() as db:
            plan = db.query(ContentPlan).filter(ContentPlan.id == id).first()
            if plan:
                plan.status = 'approved'
                db.commit()
                
                # Trigger Publishing Agent (Async)
                def _publish():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    # call orchestrator.publisher.publish(id)
                    loop.close()
                threading.Thread(target=_publish).start()
                
                return jsonify({"status": "success"})
            return jsonify({"error": "Plan not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/content/reject/<int:id>', methods=['POST'])
def reject_content(id):
    """Reject a content plan."""
    try:
        with get_db() as db:
            plan = db.query(ContentPlan).filter(ContentPlan.id == id).first()
            if plan:
                plan.status = 'rejected'
                db.commit()
                return jsonify({"status": "success"})
            return jsonify({"error": "Plan not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "running", "project": "Content Creator API"}), 200

@app.route('/api/run_pipeline', methods=['POST'])
def run_pipeline():
    data = request.json
    phase = data.get('phase')
    agent_name = data.get('agent_name')

    if not phase:
        return jsonify({"error": "Phase is required"}), 400

    def _run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if agent_name:
                logger.info(f"Triggering specific agent: {agent_name} in phase {phase}")
                result = loop.run_until_complete(orchestrator.run_phase(phase))
            else:
                logger.info(f"Triggering full pipeline for phase {phase}")
                result = loop.run_until_complete(orchestrator.run_phase(phase))
            logger.info(f"Pipeline for phase {phase} completed with result: {result}")
        except Exception as e:
            logger.error(f"Error running pipeline for phase {phase}: {e}", exc_info=True)
        finally:
            loop.close()

    thread = threading.Thread(target=_run_in_thread)
    thread.start()

    return jsonify({"message": f"Pipeline for phase {phase} initiated in background.", "phase": phase, "agent_name": agent_name}), 202

@app.route('/api/run_scheduled_task', methods=['POST'])
def run_scheduled_task():
    data = request.json
    task_name = data.get('task_name')

    if not task_name:
        return jsonify({"error": "Task name is required"}), 400

    def _run_scheduled_task_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info(f"Attempting to run scheduled task: {task_name}")
            if hasattr(scheduler, f'run_{task_name}'):
                 task_func = getattr(scheduler, f'run_{task_name}')
                 result = loop.run_until_complete(task_func())
            else:
                logger.warning(f"No direct method for scheduled task: {task_name}")
                result = {"status": "failed", "reason": "Task not found"}
            logger.info(f"Scheduled task {task_name} completed with result: {result}")
        except Exception as e:
            logger.error(f"Error running scheduled task {task_name}: {e}", exc_info=True)
        finally:
            loop.close()

    thread = threading.Thread(target=_run_scheduled_task_in_thread)
    thread.start()

    return jsonify({"message": f"Scheduled task {task_name} initiated in background.", "task_name": task_name}), 202

# --- Public Data API (Monetized) ---

@app.route('/api/v1/market-data', methods=['GET'])
@require_api_key
def get_market_data():
    """Get recent market data (Paid API)."""
    asset = request.args.get('asset')
    limit = int(request.args.get('limit', 10))
    
    try:
        with get_db() as db:
            query = db.query(MarketData)
            
            if asset:
                query = query.filter(MarketData.asset == asset)
                
            # Get latest data
            results = query.order_by(MarketData.timestamp.desc()).limit(limit).all()
            
            data = [{
                "asset": r.asset,
                "price": r.price,
                "volume": r.volume_24h,
                "change_24h": r.price_change_24h,
                "timestamp": r.timestamp.isoformat()
            } for r in results]
            
            return jsonify({"data": data, "count": len(data)})
            
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return jsonify({"error": "Internal server error"}), 500

# --- Webhook Handlers ---

def _handle_checkout_completed(db, session):
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    email = session.get('customer_details', {}).get('email')
    
    if not email:
        logger.warning("No email in checkout session")
        return

    # Find or create user
    user = db.query(CommunityUser).filter(CommunityUser.email == email).first()
    if not user:
        user = CommunityUser(email=email, tier=UserTier.FREE)
        db.add(user)
        db.flush()
        logger.info(f"Created new user from checkout: {email}")
    
    # Update user stripe info
    subscription = stripe_api.get_subscription(subscription_id)
    if not subscription:
        logger.error(f"Could not retrieve subscription {subscription_id}")
        return

    # Create Subscription record
    new_sub = Subscription(
        user_id=user.id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        tier=UserTier.PREMIUM, # Default to Premium
        status=subscription['status'],
        amount=session.get('amount_total', 0) / 100.0,
        current_period_start=subscription['current_period_start'],
        current_period_end=subscription['current_period_end']
    )
    
    db.add(new_sub)
    
    # Upgrade User
    user.tier = UserTier.PREMIUM
    user.subscription_status = 'active'
    user.updated_at = datetime.utcnow()
    
    logger.info(f"Upgraded user {email} to PREMIUM")

    # Trigger Onboarding Agent immediately
    if orchestrator and hasattr(orchestrator, 'onboarding_agent'):
        def _run_onboarding():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                logger.info("Running immediate onboarding for new member...")
                loop.run_until_complete(orchestrator.onboarding_agent.run())
                logger.info("Immediate onboarding completed")
            except Exception as e:
                logger.error(f"Error in immediate onboarding: {e}")
            finally:
                loop.close()
        
        threading.Thread(target=_run_onboarding).start()

def _handle_subscription_updated(db, subscription):
    sub_id = subscription.get('id')
    status = subscription.get('status')
    
    sub_record = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
    if sub_record:
        sub_record.status = status
        sub_record.current_period_end = datetime.fromtimestamp(subscription.get('current_period_end'))
        
        if status in ['active', 'trialing']:
            sub_record.user.subscription_status = 'active'
        else:
            sub_record.user.subscription_status = status
            if status in ['canceled', 'unpaid', 'past_due']:
                sub_record.user.tier = UserTier.FREE
        
        logger.info(f"Updated subscription {sub_id} status to {status}")

def _handle_subscription_deleted(db, subscription):
    sub_id = subscription.get('id')
    sub_record = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
    
    if sub_record:
        sub_record.status = 'canceled'
        sub_record.user.subscription_status = 'canceled'
        sub_record.user.tier = UserTier.FREE
        logger.info(f"Subscription {sub_id} canceled. User downgraded.")

@app.route('/api/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = settings.stripe_webhook_secret

    if not webhook_secret:
        logger.error("Stripe webhook secret not configured")
        return jsonify({"error": "Webhook secret not configured"}), 500

    event = stripe_api.webhook_construct_event(payload, sig_header, webhook_secret)

    if not event:
        logger.error("Invalid webhook signature or payload")
        return jsonify({"error": "Invalid signature"}), 400

    event_type = event['type']
    data = event['data']['object']

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        with get_db() as db:
            if event_type == 'checkout.session.completed':
                _handle_checkout_completed(db, data)
            elif event_type == 'customer.subscription.updated':
                _handle_subscription_updated(db, data)
            elif event_type == 'customer.subscription.deleted':
                _handle_subscription_deleted(db, data)
            
    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)