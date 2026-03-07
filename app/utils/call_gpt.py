from openai import OpenAI

def call_gpt(client: OpenAI, prompt: str, model="gpt-4.1-nano-2025-04-14", ensure_json=True) -> str:
    if ensure_json:
        response = client.responses.create(
            model=model,
            input=prompt,
            text={"format": { "type": "json_object"} }
            # response_format={"type": "json_schema",
                            #  "json_schema": {
                            #     "name": "CalendarEvent",
                            #     "schema": {
                            #         "type": "object",
                            #         "properties": {
                            #             "name": {"type": "string"},
                            #             "date": {"type": "string"},
                            #             "participants": {
                            #                 "type": "array",
                            #                 "items": {"type": "string"}
                            #             }
                            #         },
                            #         "required": ["name", "date", "participants"],
                            #         "additionalProperties": False
                            #     }
                            # }
            # }
        )
    else:
        response = client.responses.create(
            model=model,
            input=prompt
        )
    return response.output_text
