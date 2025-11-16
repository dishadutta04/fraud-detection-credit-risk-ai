from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
from .credit_agent import CreditAssessmentAgent
from .fraud_agent import FraudDetectionAgent

# Define state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str
    task_type: str
    data: dict
    result: dict

class OrchestratorAgent:
    def __init__(self):
        self.credit_agent = CreditAssessmentAgent()
        self.fraud_agent = FraudDetectionAgent()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("router", self._route_request)
        workflow.add_node("credit_agent", self._credit_node)
        workflow.add_node("fraud_agent", self._fraud_node)
        workflow.add_node("finalizer", self._finalize_result)
        
        # Add edges
        workflow.set_entry_point("router")
        workflow.add_conditional_edges(
            "router",
            self._determine_next_agent,
            {
                "credit": "credit_agent",
                "fraud": "fraud_agent",
                "end": "finalizer"
            }
        )
        workflow.add_edge("credit_agent", "finalizer")
        workflow.add_edge("fraud_agent", "finalizer")
        workflow.add_edge("finalizer", END)
        
        return workflow.compile()
    
    def _route_request(self, state: AgentState) -> AgentState:
        """Determine which agent should handle the request"""
        task_type = state.get("task_type", "")
        
        if "credit" in task_type.lower():
            state["next_agent"] = "credit"
        elif "fraud" in task_type.lower():
            state["next_agent"] = "fraud"
        else:
            state["next_agent"] = "end"
        
        return state
    
    def _determine_next_agent(self, state: AgentState) -> str:
        """Conditional edge function"""
        return state.get("next_agent", "end")
    
    def _credit_node(self, state: AgentState) -> AgentState:
        """Process credit assessment"""
        result = self.credit_agent.assess_application(state["data"])
        state["result"] = result
        state["messages"].append(AIMessage(content=f"Credit assessment completed: {result['decision']}"))
        return state
    
    def _fraud_node(self, state: AgentState) -> AgentState:
        """Process fraud detection"""
        result = self.fraud_agent.check_transaction(state["data"])
        state["result"] = result
        state["messages"].append(AIMessage(content=f"Fraud check completed: {result['action']}"))
        return state
    
    def _finalize_result(self, state: AgentState) -> AgentState:
        """Finalize and return result"""
        return state
    
    def process_request(self, task_type: str, data: dict) -> dict:
        """Main entry point for orchestrator"""
        
        initial_state = {
            "messages": [HumanMessage(content=f"Processing {task_type} request")],
            "task_type": task_type,
            "data": data,
            "next_agent": "",
            "result": {}
        }
        
        # Run graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state["result"]
