"""
Base Agent Class
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import settings
from app.utils.logger import logger
from app.orchestration.state_schema import AgentState


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, agent_name: str):
        """
        Initialize base agent
        
        Args:
            agent_name: Name of the agent
        """
        self.agent_name = agent_name
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        logger.info(f"Initialized {agent_name}")
    
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute agent logic
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        pass
    
    def _create_prompt(self, template: str, **kwargs) -> ChatPromptTemplate:
        """
        Create chat prompt template
        
        Args:
            template: Prompt template string
            **kwargs: Template variables
            
        Returns:
            ChatPromptTemplate instance
        """
        return ChatPromptTemplate.from_template(template)
    
    async def _invoke_llm(
        self,
        prompt_template: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Invoke LLM with prompt
        
        Args:
            prompt_template: Prompt template string
            variables: Template variables
            
        Returns:
            LLM response
        """
        try:
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm
            
            response = await chain.ainvoke(variables)
            return response.content
            
        except Exception as e:
            logger.error(f"{self.agent_name} LLM invocation error: {e}")
            raise
    
    def _update_state(
        self,
        state: AgentState,
        updates: Dict[str, Any]
    ) -> AgentState:
        """
        Update agent state with new values
        
        Args:
            state: Current state
            updates: Updates to apply
            
        Returns:
            Updated state
        """
        updated_state = state.copy()
        updated_state.update(updates)
        updated_state["updated_at"] = datetime.utcnow()
        updated_state["current_agent"] = self.agent_name
        
        # Add to completed agents if not already there
        if self.agent_name not in updated_state.get("completed_agents", []):
            completed = updated_state.get("completed_agents", [])
            completed.append(self.agent_name)
            updated_state["completed_agents"] = completed
        
        return updated_state
    
    def _log_error(self, state: AgentState, error_message: str) -> AgentState:
        """
        Log error in state
        
        Args:
            state: Current state
            error_message: Error message
            
        Returns:
            Updated state with error
        """
        errors = state.get("errors", [])
        errors.append(f"{self.agent_name}: {error_message}")
        
        return self._update_state(state, {"errors": errors})
    
    def _log_warning(self, state: AgentState, warning_message: str) -> AgentState:
        """
        Log warning in state
        
        Args:
            state: Current state
            warning_message: Warning message
            
        Returns:
            Updated state with warning
        """
        warnings = state.get("warnings", [])
        warnings.append(f"{self.agent_name}: {warning_message}")
        
        return self._update_state(state, {"warnings": warnings})
    
    def _get_context(self, state: AgentState) -> str:
        """
        Build context string from state
        
        Args:
            state: Current state
            
        Returns:
            Context string
        """
        context_parts = [
            f"Event: {state.get('event_name', 'Unknown')}",
            f"Type: {state.get('event_type', 'Unknown')}",
            f"Theme: {state.get('event_theme', 'Unknown')}",
            f"Target Audience: {state.get('target_audience', 'Unknown')}",
            f"Participants: {state.get('participant_count', 0)}",
        ]
        
        if state.get("event_description"):
            context_parts.append(f"Description: {state['event_description']}")
        
        return "\n".join(context_parts)
    
    async def _save_output(
        self,
        state: AgentState,
        output_key: str,
        output_value: Any
    ) -> AgentState:
        """
        Save agent output to state
        
        Args:
            state: Current state
            output_key: Key for output
            output_value: Output value
            
        Returns:
            Updated state
        """
        agent_outputs = state.get("agent_outputs", {})
        agent_outputs[self.agent_name] = {
            output_key: output_value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self._update_state(state, {"agent_outputs": agent_outputs})
    
    def should_execute(self, state: AgentState, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if agent should execute based on state and config
        
        Args:
            state: Current state
            config: Workflow configuration
            
        Returns:
            True if should execute, False otherwise
        """
        # Default: always execute
        # Subclasses can override with specific logic
        return True
    
    def get_execution_time(self) -> float:
        """
        Get execution time for logging
        
        Returns:
            Execution time in milliseconds
        """
        if hasattr(self, '_start_time'):
            from datetime import datetime
            delta = datetime.utcnow() - self._start_time
            return delta.total_seconds() * 1000
        return 0.0
    
    def start_execution(self) -> None:
        """Mark start of execution"""
        self._start_time = datetime.utcnow()
        logger.info(f"{self.agent_name} starting execution")
    
    def end_execution(self) -> None:
        """Mark end of execution"""
        execution_time = self.get_execution_time()
        logger.info(f"{self.agent_name} completed in {execution_time:.2f}ms")