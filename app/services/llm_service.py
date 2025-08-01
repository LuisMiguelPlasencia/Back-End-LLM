from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import openai
import anthropic
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from LLM"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        try:
            messages = []
            
            if context:
                messages.append({
                    "role": "system",
                    "content": f"You are a helpful assistant. Context from audio transcription: {context}"
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return {
                "text": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model_used": response.model
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider"""
    
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        try:
            system_prompt = "You are a helpful assistant."
            if context:
                system_prompt += f" Context from audio transcription: {context}"
            
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "text": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "model_used": response.model
            }
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")


class LLMService:
    """Main LLM service with provider abstraction"""
    
    def __init__(self, provider: str = "openai"):
        self.provider_name = provider
        self.provider = self._get_provider(provider)
    
    def _get_provider(self, provider: str) -> LLMProvider:
        """Get LLM provider instance"""
        if provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            return OpenAIProvider()
        elif provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            return AnthropicProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    async def generate_chat_response(
        self, 
        user_message: str, 
        transcription_text: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate chat response with optional transcription context"""
        if provider:
            self.provider = self._get_provider(provider)
        
        try:
            result = await self.provider.generate_response(
                prompt=user_message,
                context=transcription_text
            )
            
            logger.info(f"Generated response using {self.provider_name}: {result['tokens_used']} tokens")
            return result
            
        except Exception as e:
            logger.error(f"LLM service error: {e}")
            raise 