"""LLM Client with automatic failover support."""

from typing import Optional, Dict, Any
import time
from loguru import logger
from anthropic import Anthropic
import google.generativeai as genai

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str = ""
    google_api_key: str = ""
    google_api_key_backup: str = ""
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()


class LLMClientWithFailover:
    """
    LLM Client that supports multiple API keys with automatic failover.
    
    When a rate limit is hit, automatically switches to backup key.
    """
    
    def __init__(self):
        """Initialize LLM clients."""
        self.anthropic_client = None
        self.gemini_client = None
        self.gemini_backup_client = None
        
        # Track which Gemini key is currently active
        self.active_gemini_key = "primary"
        self.last_failover_time = 0
        self.failover_cooldown = 60  # Wait 60s before trying primary again
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all available LLM clients."""
        # Anthropic/Claude
        if settings.anthropic_api_key and not settings.anthropic_api_key.startswith("sk-ant-test"):
            try:
                self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")
        
        # Google Gemini (primary)
        if settings.google_api_key and not settings.google_api_key.startswith("test"):
            try:
                genai.configure(api_key=settings.google_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("Gemini client initialized (primary key)")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini primary: {e}")
        
        # Google Gemini (backup)
        if settings.google_api_key_backup:
            try:
                # We'll configure this when needed for failover
                logger.info("Gemini backup key available")
            except Exception as e:
                logger.warning(f"Failed to setup Gemini backup: {e}")
    
    def generate_with_claude(self, prompt: str, max_tokens: int = 1000, **kwargs) -> str:
        """
        Generate content using Claude.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments for the API
            
        Returns:
            Generated text
        """
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized. Check ANTHROPIC_API_KEY in .env")
        
        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    def generate_with_gemini(self, prompt: str, **kwargs) -> str:
        """
        Generate content using Gemini with automatic failover.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments for the API
            
        Returns:
            Generated text
        """
        # Try primary key first (unless we recently failed over)
        if self.active_gemini_key == "backup":
            # Check if cooldown period has passed
            if time.time() - self.last_failover_time > self.failover_cooldown:
                self.active_gemini_key = "primary"
                logger.info("Cooldown expired, switching back to primary Gemini key")
        
        try:
            if self.active_gemini_key == "primary":
                if not self.gemini_client:
                    raise ValueError("Gemini primary client not initialized")
                
                response = self.gemini_client.generate_content(prompt, **kwargs)
                return response.text
                
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
                logger.warning(f"Gemini primary key hit rate limit: {e}")
                
                # Try backup key
                if settings.google_api_key_backup:
                    logger.info("Switching to Gemini backup key...")
                    return self._use_gemini_backup(prompt, **kwargs)
                else:
                    raise ValueError("Gemini rate limit hit and no backup key available")
            else:
                # Non-rate-limit error, re-raise
                logger.error(f"Gemini API error: {e}")
                raise
    
    def _use_gemini_backup(self, prompt: str, **kwargs) -> str:
        """Use the backup Gemini key."""
        try:
            # Reconfigure with backup key
            genai.configure(api_key=settings.google_api_key_backup)
            backup_model = genai.GenerativeModel('gemini-2.5-flash')
            
            response = backup_model.generate_content(prompt, **kwargs)
            
            # Mark that we're using backup
            self.active_gemini_key = "backup"
            self.last_failover_time = time.time()
            
            logger.success("Successfully switched to Gemini backup key")
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini backup key also failed: {e}")
            
            # Try to switch back to primary configuration
            if settings.google_api_key:
                genai.configure(api_key=settings.google_api_key)
                self.active_gemini_key = "primary"
            
            raise
    
    def generate(
        self, 
        prompt: str, 
        model: str = "gemini", 
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Generate content using specified model with fallback.
        
        Args:
            prompt: The prompt to send
            model: Model to use ("claude", "gemini")
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments
            
        Returns:
            Generated text
        """
        if model == "claude" or model == "anthropic":
            return self.generate_with_claude(prompt, max_tokens, **kwargs)
        elif model == "gemini" or model == "google":
            return self.generate_with_gemini(prompt, **kwargs)
        else:
            raise ValueError(f"Unknown model: {model}")
    
    def get_active_gemini_key(self) -> str:
        """Get which Gemini key is currently active."""
        return self.active_gemini_key


# Global instance
llm_client = LLMClientWithFailover()
