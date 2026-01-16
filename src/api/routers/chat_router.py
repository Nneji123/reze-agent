"""Chat router for Reze AI Agent.

This router provides the ONLY interface to interact with Reze.
All interactions happen through chat, where the agent uses tools
to perform actions like sending emails, checking status, etc.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from src.api.schemas.chat import (
    ChatRequest,
    ConversationDeletedResponse,
    ConversationHistoryResponse,
    ConversationsListResponse,
)
from src.services.conversation import conversation_service
from src.services.prompt import REZE_INSTRUCTIONS
from src.services.rag import rag_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/message", summary="Chat with Reze AI Agent (Streaming)")
async def chat_message(request: ChatRequest):
    """
    Send a message to Reze AI Agent and receive streaming response.

    This is the ONLY way to interact with Reze. The agent will:
    1. Understand your request naturally
    2. Ask questions if information is missing
    3. Call tools (send_email, get_status, etc.) when appropriate
    4. Stream response in real-time

    ## Example Flow:
    ```
    You: "Send an email to john@example.com"
    Reze: "Sure! What should the subject be?"

    You: "Welcome email"
    Reze: "Got it. What should the email say?"

    You: "Just a simple welcome message"
    Reze: [Uses send_email tool] "Email sent! ID: abc123"
    ```

    ## Request Body:
    - **message**: Your message to the agent (required)
    - **conversation_id**: Track conversation (optional, auto-generated if not provided)
    - **streaming**: Always true for this endpoint

    ## Response:
    Returns StreamingResponse with real-time chunks
    """
    try:
        if not request.conversation_id:
            conversation_id = await conversation_service.create_conversation(
                username=request.username
            )
            logger.info(
                f"Created new conversation: {conversation_id} for user: {request.username}"
            )
        else:
            conversation_id = request.conversation_id

        await conversation_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            username=request.username,
        )

        history = await conversation_service.get_conversation_history(
            conversation_id=conversation_id,
            limit=20,
        )

        conversation_context = []
        for msg in history:
            if msg.role in ["user", "assistant"]:
                conversation_context.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                    }
                )

        async def stream_chat():
            """Stream agent response in real-time."""
            full_response = ""

            try:
                async for chunk in rag_service.query_stream(
                    query=request.message,
                    conversation_history=conversation_context,
                    use_rag=True,
                ):
                    full_response += chunk
                    yield chunk

                await conversation_service.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                )

                logger.info(f"Response generated for conversation {conversation_id}")

            except Exception as e:
                logger.error(f"Streaming error for conversation {conversation_id}: {e}")
                error_msg = f"\n\n[Error: {str(e)}]"
                full_response += error_msg
                yield error_msg

                await conversation_service.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=error_msg,
                )

        return StreamingResponse(
            stream_chat(),
            media_type="text/plain",
            headers={
                "X-Conversation-ID": conversation_id,
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/conversations/{username}",
    summary="Get user conversations",
    response_model=ConversationsListResponse,
)
async def list_user_conversations(username: str):
    """
    List all conversations for a specific user.

    Returns a list of conversation IDs with metadata.
    """
    try:
        conversations = await conversation_service.get_user_conversations(
            username=username
        )

        conversation_ids = [conv["conversation_id"] for conv in conversations]

        return ConversationsListResponse(
            conversations=conversation_ids,
            total=len(conversation_ids),
        )
    except Exception as e:
        logger.error(f"Failed to list conversations for {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/conversations/{conversation_id}/history",
    summary="Get conversation history",
    response_model=ConversationHistoryResponse,
)
async def get_conversation_history(conversation_id: str):
    """
    Retrieve full conversation history for a specific session.

    Returns all messages (user and assistant) in chronological order.
    Useful for debugging or reviewing past interactions.

    ## Path Parameters:
    - **conversation_id**: The unique conversation identifier

    ## Returns:
    - conversation_id: The conversation identifier
    - messages: List of all messages
    - message_count: Total number of messages
    """
    try:
        messages = await conversation_service.get_conversation_history(
            conversation_id=conversation_id,
            limit=None,  # Get all messages
        )

        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=messages,
            message_count=len(messages),
        )
    except Exception as e:
        logger.error(f"Failed to get conversation history for {conversation_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Conversation not found: {str(e)}")


@router.delete(
    "/conversations/{conversation_id}",
    summary="Delete conversation",
    response_model=ConversationDeletedResponse,
)
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and all its messages.

    This permanently removes the conversation history.
    Useful for starting fresh or managing storage.

    ## Path Parameters:
    - **conversation_id**: The unique conversation identifier to delete

    ## Returns:
    - conversation_id: ID of deleted conversation
    - deleted: Confirmation that deletion was successful
    """
    try:
        await conversation_service.delete_conversation(conversation_id=conversation_id)

        logger.info(f"Deleted conversation: {conversation_id}")

        return ConversationDeletedResponse(
            conversation_id=conversation_id,
            deleted=True,
        )
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-prompt", summary="Get system prompt (for debugging)")
async def get_system_prompt():
    """
    Get the current system prompt being used by Reze.

    Useful for debugging to understand agent's instructions.
    """
    return {
        "system_prompt": REZE_INSTRUCTIONS,
        "length": len(REZE_INSTRUCTIONS),
    }
