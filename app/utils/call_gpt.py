from openai import OpenAI

def call_gpt(client: OpenAI, prompt: str, model="gpt-4.1-nano-2025-04-14") -> str:

    response = client.responses.create(
        model=model,
        input=prompt,
        
    )
    return response.output_text