from fastapi import APIRouter, HTTPException, BackgroundTasks
from langchain_core.messages import HumanMessage
from langgraph.graph import END

from app.schemas import IntegrationCreate, IntegrationResponse, ChatRequest, ChatResponse
from app.services.security import save_credential
from app.services.mcp_bridge import OpenAPIMCPBridge
from app.services.tool_registry import ToolRegistry
from app.services.security import save_credential
from app.core.agent import agent_app, registry as global_registry
from sqlmodel import Session
from app.core.database import engine, ChatMessage

router = APIRouter()


@router.post("/integrations", response_model=IntegrationResponse)
async def add_integration(data: IntegrationCreate):
    '''
        creates tools when given name, spec url and the credentials
        also updates the global registry (adds new tools there)
    '''

    try:
        connection_id = data.name.lower().replace(" ", "-")

        save_credential(
            connection_id=connection_id,
            api_key=data.api_key,
            name=data.name,
            spec_url=data.spec_url
        )

        bridge = OpenAPIMCPBridge(data.name, data.spec_url, connection_id)

        bridge.register_tools()
        tools = bridge.get_tools()

        global_registry.register_tools(tools)

        return IntegrationResponse(
            message=f"Successfully connected {data.name}",
            tools_count=len(tools)
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Talk to the Agent.
    """
    try:
        input_state = {
            "messages": [HumanMessage(content=request.message)],

        }

        config = {"configurable": {"thread_id": request.thread_id}}

        final_response = ""
        tool_logs = []

        result = agent_app.invoke(input_state, config=config)

        last_msg = result["messages"][-1]
        final_response = last_msg.content

        # extracting tool calls debugging
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_logs.extend(msg.tool_calls)

        with Session(engine) as session:
            session.add(ChatMessage(thread_id=request.thread_id,
                        role="user", content=request.message))
            session.add(ChatMessage(thread_id=request.thread_id,
                        role="assistant", content=str(final_response)))
            session.commit()

        return ChatResponse(
            response=str(final_response),
            tool_calls=tool_logs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
