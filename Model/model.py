from utils.safeExecution import safeExecution
from transformers import TextIteratorStreamer
from threading import Thread
import time
@safeExecution
def generate_response(inputs, model, tokenizer,max_tokens, temperature=0.7):
    start = time.time()
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True,skip_special_tokens=True)
    generation_kwargs = dict(
        **inputs,
        max_new_tokens=max_tokens,
        do_sample=True,
        temperature=temperature,
        streamer=streamer,
        eos_token_id=tokenizer.eos_token_id,
    )
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    return streamer


@safeExecution
def format_user_query(query, ordered_documents, ordered_chats):
    content = "\n\n".join(ordered_documents + ordered_chats)

    system_prompt = f"""
    You are a helpful assistant.

    Answer the user ONLY using the provided context.
    If the answer is not in the context, say "I don't know".

    <context>
    {content}
    </context>
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    return messages


@safeExecution
def format_messages(messages, Tokenizer):
    templated = Tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        return_tensors="pt",
        add_generation_prompt=True,
        return_dict=True,
    )
    return templated


@safeExecution
def text_to_tokens(text, Tokenizer, max_length=512):
    return Tokenizer(
        text, return_tensors="pt", padding=True, truncation=True, max_length=max_length
    )


@safeExecution
def tokens_to_text(tokens, Tokenizer):
    return Tokenizer.decode(tokens, skip_special_tokens=True)


"""
    # message = format_user_query(query, ordered_documents, ordered_chats)

    # inputs = format_messages(message, tokenizer)

    # streamer = generate_response(
    #     inputs,
    #     model,
    #     tokenizer,
    #     200,
    #     creativity_levels[creativity],
    # )
"""

# {%- if tools %}
#     {{- '<|im_start|>system\n' }}
#     {%- if messages[0]['role'] == 'system' %}
#         {{- messages[0]['content'] }}
#     {%- else %}
#         {{- 'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.' }}
#     {%- endif %}
#     {{- "\n\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>" }}
#     {%- for tool in tools %}
#         {{- "\n" }}
#         {{- tool | tojson }}
#     {%- endfor %}
#     {{- "\n</tools>\n\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{\"name\": <function-name>, \"arguments\": <args-json-object>}\n</tool_call><|im_end|>\n" }}
# {%- else %}
#     {%- if messages[0]['role'] == 'system' %}
#         {{- '<|im_start|>system\n' + messages[0]['content'] + '<|im_end|>\n' }}
#     {%- else %}
#         {{- '<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n' }}
#     {%- endif %}
# {%- endif %}
# {%- for message in messages %}
#     {%- if (message.role == "user") or (message.role == "system" and not loop.first) or (message.role == "assistant" and not message.tool_calls) %}
#         {{- '<|im_start|>' + message.role + '\n' + message.content + '<|im_end|>' + '\n' }}
#     {%- elif message.role == "assistant" %}
#         {{- '<|im_start|>' + message.role }}
#         {%- if message.content %}
#             {{- '\n' + message.content }}
#         {%- endif %}
#         {%- for tool_call in message.tool_calls %}
#             {%- if tool_call.function is defined %}
#                 {%- set tool_call = tool_call.function %}
#             {%- endif %}
#             {{- '\n<tool_call>\n{"name": "' }}
#             {{- tool_call.name }}
#             {{- '", "arguments": ' }}
#             {{- tool_call.arguments | tojson }}
#             {{- '}\n</tool_call>' }}
#         {%- endfor %}
#         {{- '<|im_end|>\n' }}
#     {%- elif message.role == "tool" %}
#         {%- if (loop.index0 == 0) or (messages[loop.index0 - 1].role != "tool") %}
#             {{- '<|im_start|>user' }}
#         {%- endif %}
#         {{- '\n<tool_response>\n' }}
#         {{- message.content }}
#         {{- '\n</tool_response>' }}
#         {%- if loop.last or (messages[loop.index0 + 1].role != "tool") %}
#             {{- '<|im_end|>\n' }}
#         {%- endif %}
#     {%- endif %}
# {%- endfor %}
# {%- if add_generation_prompt %}
#     {{- '<|im_start|>assistant\n' }}
# {%- endif %}
