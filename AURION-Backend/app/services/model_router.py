# app/services/model_router.py
"""
Model Router - Intelligently routes queries to best AI model
Routes simple tasks to Groq (free, fast), complex to Gemini Pro (powerful)
Saves 90% on costs while maintaining quality
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Model tiers ordered by capability and cost"""
    FAST = "fast"           # Groq llama-3.3-70b (free, 500 tokens/sec)
    BALANCED = "balanced"   # Gemini 1.5 Flash ($0.075 per 1M tokens)
    POWERFUL = "powerful"   # Gemini 1.5 Pro ($1.25 per 1M tokens)
    PREMIUM = "premium"     # GPT-4 (backup, expensive)


class QueryComplexity(str, Enum):
    """Query complexity levels"""
    SIMPLE = "simple"           # Yes/no, facts, definitions
    MEDIUM = "medium"           # Explanations, comparisons, summaries
    COMPLEX = "complex"         # Analysis, reasoning, multi-step
    CREATIVE = "creative"       # Story generation, coding, design


class ModelRouter:
    """
    Routes queries to optimal AI model based on complexity
    Goal: Save costs while maintaining quality
    """
    
    def __init__(self):
        # Model configurations
        self.model_configs = {
            ModelTier.FAST: {
                'provider': 'groq',
                'model': 'llama-3.3-70b-versatile',
                'max_tokens': 2048,
                'temperature': 0.7,
                'cost_per_1m_tokens': 0.0,  # Free!
                'speed': 500,  # tokens/sec
                'best_for': ['factual', 'simple_qa', 'quick_response']
            },
            ModelTier.BALANCED: {
                'provider': 'gemini',
                'model': 'gemini-1.5-flash',
                'max_tokens': 4096,
                'temperature': 0.8,
                'cost_per_1m_tokens': 0.075,
                'speed': 200,
                'best_for': ['clarify', 'conversational', 'informational_search']
            },
            ModelTier.POWERFUL: {
                'provider': 'gemini',
                'model': 'gemini-1.5-pro',
                'max_tokens': 8192,
                'temperature': 0.9,
                'cost_per_1m_tokens': 1.25,
                'speed': 100,
                'best_for': ['complex_reasoning', 'deep_analysis', 'autonomous_agent']
            },
            ModelTier.PREMIUM: {
                'provider': 'openai',
                'model': 'gpt-4-turbo',
                'max_tokens': 4096,
                'temperature': 0.8,
                'cost_per_1m_tokens': 10.0,
                'speed': 50,
                'best_for': ['fallback', 'critical_tasks']
            }
        }
        
        # Complexity patterns
        self.complexity_indicators = {
            QueryComplexity.SIMPLE: [
                'what is', 'who is', 'when was', 'where is',
                'define', 'meaning of', 'yes or no',
                'true or false', 'is it', 'does it'
            ],
            QueryComplexity.MEDIUM: [
                'explain', 'how to', 'why', 'compare',
                'difference between', 'summarize', 'describe',
                'tell me about', 'what are the'
            ],
            QueryComplexity.COMPLEX: [
                'analyze', 'evaluate', 'assess', 'critique',
                'pros and cons', 'advantages disadvantages',
                'in depth', 'detailed analysis', 'reasoning'
            ],
            QueryComplexity.CREATIVE: [
                'write', 'create', 'design', 'generate',
                'come up with', 'invent', 'imagine', 'story'
            ]
        }
        
        # Intent to tier mapping
        self.intent_tier_map = {
            'factual': ModelTier.FAST,
            'clarify': ModelTier.BALANCED,
            'conversational': ModelTier.BALANCED,
            'live_search': ModelTier.BALANCED,
            'local_search': ModelTier.BALANCED,
            'informational_search': ModelTier.BALANCED,
            'web_search': ModelTier.BALANCED,
            'complex_reasoning': ModelTier.POWERFUL,
            'autonomous_agent': ModelTier.POWERFUL,
            'task_automation': ModelTier.POWERFUL
        }
        
        logger.info("✅ ModelRouter initialized with 4-tier system")
    
    def route(
        self,
        query: str,
        intent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        prefer_tier: Optional[ModelTier] = None
    ) -> Dict[str, Any]:
        """
        Route query to best model
        
        Args:
            query: User query
            intent: Detected intent
            context: Conversation context
            prefer_tier: Preferred tier (optional override)
        
        Returns:
            {
                'tier': ModelTier,
                'provider': str,
                'model': str,
                'config': dict,
                'reasoning': str
            }
        """
        
        # If explicit preference provided
        if prefer_tier:
            config = self.model_configs[prefer_tier]
            return {
                'tier': prefer_tier,
                'provider': config['provider'],
                'model': config['model'],
                'config': config,
                'reasoning': f"Explicit preference: {prefer_tier}"
            }
        
        # Route by intent first
        if intent and intent in self.intent_tier_map:
            tier = self.intent_tier_map[intent]
            config = self.model_configs[tier]
            
            logger.info(f"🎯 Routing {intent} to {tier} ({config['model']})")
            
            return {
                'tier': tier,
                'provider': config['provider'],
                'model': config['model'],
                'config': config,
                'reasoning': f"Intent-based: {intent} → {tier}"
            }
        
        # Analyze query complexity
        complexity = self._analyze_complexity(query)
        tier = self._complexity_to_tier(complexity)
        config = self.model_configs[tier]
        
        logger.info(f"🎯 Routing {complexity} query to {tier} ({config['model']})")
        
        return {
            'tier': tier,
            'provider': config['provider'],
            'model': config['model'],
            'config': config,
            'reasoning': f"Complexity-based: {complexity} → {tier}"
        }
    
    def _analyze_complexity(self, query: str) -> QueryComplexity:
        """Analyze query complexity"""
        query_lower = query.lower()
        
        # Check for complexity indicators
        for complexity, patterns in self.complexity_indicators.items():
            if any(pattern in query_lower for pattern in patterns):
                return complexity
        
        # Analyze query length and structure
        word_count = len(query.split())
        
        if word_count <= 5:
            return QueryComplexity.SIMPLE
        elif word_count <= 15:
            return QueryComplexity.MEDIUM
        else:
            return QueryComplexity.COMPLEX
    
    def _complexity_to_tier(self, complexity: QueryComplexity) -> ModelTier:
        """Map complexity to model tier"""
        mapping = {
            QueryComplexity.SIMPLE: ModelTier.FAST,
            QueryComplexity.MEDIUM: ModelTier.BALANCED,
            QueryComplexity.COMPLEX: ModelTier.POWERFUL,
            QueryComplexity.CREATIVE: ModelTier.POWERFUL
        }
        
        return mapping.get(complexity, ModelTier.BALANCED)
    
    async def execute_with_fallback(
        self,
        query: str,
        intent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        ai_service=None
    ) -> Dict[str, Any]:
        """
        Execute query with automatic fallback
        
        Tries: Primary model → Next tier → Next tier → Premium
        """
        
        # Get primary routing
        route_info = self.route(query, intent, context)
        primary_tier = route_info['tier']
        
        # Define fallback chain
        fallback_chain = self._get_fallback_chain(primary_tier)
        
        logger.info(f"🔄 Fallback chain: {' → '.join([t.value for t in fallback_chain])}")
        
        # Try each tier in sequence
        for tier in fallback_chain:
            try:
                config = self.model_configs[tier]
                provider = config['provider']
                model = config['model']
                
                logger.info(f"⚡ Attempting with {tier} ({model})")
                
                # Execute with this model
                result = await self._execute_with_model(
                    query=query,
                    provider=provider,
                    model=model,
                    config=config,
                    ai_service=ai_service
                )
                
                if result.get('success'):
                    logger.info(f"✅ Success with {tier}")
                    return {
                        'success': True,
                        'response': result['response'],
                        'tier_used': tier,
                        'model_used': model,
                        'fallback_count': fallback_chain.index(tier)
                    }
            
            except Exception as e:
                logger.warning(f"⚠️ {tier} failed: {str(e)}")
                continue
        
        # All models failed
        logger.error("❌ All models failed")
        return {
            'success': False,
            'error': 'All AI models failed',
            'fallback_count': len(fallback_chain)
        }
    
    def _get_fallback_chain(self, primary_tier: ModelTier) -> List[ModelTier]:
        """Get fallback chain starting from primary tier"""
        
        # All tiers in order
        all_tiers = [
            ModelTier.FAST,
            ModelTier.BALANCED,
            ModelTier.POWERFUL,
            ModelTier.PREMIUM
        ]
        
        # Start from primary, try all others
        primary_index = all_tiers.index(primary_tier)
        
        # Build chain: primary → next tier → all others
        chain = [primary_tier]
        
        # Add remaining tiers
        for tier in all_tiers:
            if tier != primary_tier:
                chain.append(tier)
        
        return chain
    
    async def _execute_with_model(
        self,
        query: str,
        provider: str,
        model: str,
        config: Dict[str, Any],
        ai_service=None
    ) -> Dict[str, Any]:
        """Execute query with specific model"""
        
        if not ai_service:
            raise Exception("AI service not provided")
        
        # Route to appropriate provider
        if provider == 'groq':
            response = await ai_service.get_groq_response(
                prompt=query,
                max_tokens=config['max_tokens'],
                temperature=config['temperature']
            )
        
        elif provider == 'gemini':
            response = await ai_service.get_gemini_response(
                prompt=query,
                model=model,
                max_tokens=config['max_tokens'],
                temperature=config['temperature']
            )
        
        elif provider == 'openai':
            response = await ai_service.get_openai_response(
                prompt=query,
                model=model,
                max_tokens=config['max_tokens'],
                temperature=config['temperature']
            )
        
        else:
            raise Exception(f"Unknown provider: {provider}")
        
        return {
            'success': True,
            'response': response
        }
    
    def estimate_cost(
        self,
        tier: ModelTier,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost for query"""
        config = self.model_configs[tier]
        cost_per_1m = config['cost_per_1m_tokens']
        
        total_tokens = input_tokens + output_tokens
        cost = (total_tokens / 1_000_000) * cost_per_1m
        
        return cost
    
    def get_cost_savings(
        self,
        fast_tier_usage: float,
        balanced_tier_usage: float,
        powerful_tier_usage: float
    ) -> Dict[str, Any]:
        """
        Calculate cost savings vs using only Gemini Pro
        
        Args:
            fast_tier_usage: % of queries routed to fast tier
            balanced_tier_usage: % to balanced
            powerful_tier_usage: % to powerful
        
        Returns:
            Savings analysis
        """
        
        # Assume 1M tokens per month
        tokens_per_month = 1_000_000
        
        # Cost if using only Gemini Pro for everything
        gemini_pro_cost = (tokens_per_month / 1_000_000) * 1.25  # $1.25
        
        # Actual cost with routing
        actual_cost = (
            (tokens_per_month * fast_tier_usage * 0.0) +
            (tokens_per_month * balanced_tier_usage * 0.075 / 1_000_000) +
            (tokens_per_month * powerful_tier_usage * 1.25 / 1_000_000)
        )
        
        savings = gemini_pro_cost - actual_cost
        savings_percent = (savings / gemini_pro_cost) * 100
        
        return {
            'baseline_cost': round(gemini_pro_cost, 2),
            'actual_cost': round(actual_cost, 2),
            'savings': round(savings, 2),
            'savings_percent': round(savings_percent, 1),
            'breakdown': {
                'fast_tier': f"{fast_tier_usage*100}% at $0",
                'balanced_tier': f"{balanced_tier_usage*100}% at $0.075/1M",
                'powerful_tier': f"{powerful_tier_usage*100}% at $1.25/1M"
            }
        }


# Create singleton instance
model_router = ModelRouter()
