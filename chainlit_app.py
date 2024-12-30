from agent import graph_builder, Config, Configurable, ToolMessage, HumanMessage, system_prompt, RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from agent import Config, Configurable
import chainlit as cl

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

@cl.on_chat_start
async def on_chat_start():
    config = Config(
            configurable=Configurable(
                thread_id=cl.context.session.id
            )
        ).model_dump()
    cb = cl.LangchainCallbackHandler()
    final_answer = cl.Message(content="")

    for msg, metadata in graph.stream(
                {
                    "messages": [
                        system_prompt,
                        HumanMessage(content="Hello!")
                    ]
                },
            stream_mode="messages",
            config=RunnableConfig(callbacks=[cb], **config)
        ):
            msg.pretty_print()
            if (
                msg.content
                and not isinstance(msg, HumanMessage)
                and not isinstance(msg, ToolMessage)
            ):
                await final_answer.stream_token(msg.content)

    await final_answer.send()

@cl.on_message
async def on_message(umsg: cl.Message):
    config = Config(
        configurable=Configurable(
            thread_id=cl.context.session.id
        )
    ).model_dump()
    cb = cl.LangchainCallbackHandler()
    final_answer = cl.Message(content="")

    if umsg.elements:
        await final_answer.stream_token("The Model currently Does not support File Input")
        await final_answer.send()
        return

    """
    if umsg.content == "Test--++--":
        res = await cl.AskActionMessage(
                content="Pick an action!",
                actions=[
                    cl.Action(name="continue", value=True, label="✅ Continue"),
                    cl.Action(name="cancel", value=False, label="❌ Cancel"),
                ],
            ).send()
        return
    """
    for msg, metadata in graph.stream(
            {
                "messages": [
                    system_prompt,
                    HumanMessage(content=umsg.content)
                ]
            },
        stream_mode="messages",
        config=RunnableConfig(callbacks=[cb], **config)
    ):
        if isinstance(msg, ToolMessage):
            msg.pretty_print()
        if (
            msg.content
            and not isinstance(msg, HumanMessage)
            and not isinstance(msg, ToolMessage)
        ):
            await final_answer.stream_token(msg.content)

    await final_answer.send()
