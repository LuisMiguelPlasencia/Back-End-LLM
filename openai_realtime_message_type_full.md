# 🎧 OpenAI Realtime API --- Message Types Reference

This document explains all known **OpenAI Realtime WebSocket message
types**, categorized into **input (client → server)** and **output
(server → client)** types, including their **purpose, usage, and
examples**.

------------------------------------------------------------------------

## 🧩 Input Message Types (Client → Server)

These are the messages your client application sends to the Realtime API
to control sessions, manage audio input, or trigger responses.

------------------------------------------------------------------------

### 1. `session.update`

**Purpose:**\
Update or modify the current session configuration such as model, voice,
temperature, modalities, or turn detection.

**Example:**

``` json
{
  "type": "session.update",
  "session": {
    "model": "gpt-4o-realtime-preview",
    "voice": "alloy",
    "temperature": 0.7,
    "input_audio_format": "pcm16",
    "output_audio_format": "wav"
  }
}
```

------------------------------------------------------------------------

### 2. `conversation.item.create`

**Purpose:**\
Add a new item (e.g., message, system instruction, or tool call) to the
conversation history.

**Example:**

``` json
{
  "type": "conversation.item.create",
  "item": {
    "type": "message",
    "role": "user",
    "content": [
      { "type": "input_text", "text": "What’s the weather like in Tokyo?" }
    ]
  }
}
```

------------------------------------------------------------------------

### 3. `conversation.item.delete`

**Purpose:**\
Remove a specific item from the conversation history by ID.

**Example:**

``` json
{
  "type": "conversation.item.delete",
  "item_id": "conv_item_42"
}
```

------------------------------------------------------------------------

### 4. `conversation.item.retrieve`

**Purpose:**\
Fetch one or more conversation items from the session history.

**Example:**

``` json
{
  "type": "conversation.item.retrieve",
  "item_ids": ["conv_item_1", "conv_item_2"]
}
```

------------------------------------------------------------------------

### 5. `conversation.item.truncate`

**Purpose:**\
Truncate or shorten the conversation history, keeping only recent
messages.

**Example:**

``` json
{
  "type": "conversation.item.truncate",
  "last_id": "conv_item_15"
}
```

------------------------------------------------------------------------

### 6. `input_audio_buffer.append`

**Purpose:**\
Append an audio chunk (base64-encoded PCM16) to the input buffer. Used
for streaming microphone input.

**Example:**

``` json
{
  "type": "input_audio_buffer.append",
  "audio": "<base64-encoded-audio>"
}
```

------------------------------------------------------------------------

### 7. `input_audio_buffer.commit`

**Purpose:**\
Tell the server that the current batch of audio has ended and should be
processed (transcription or response).

**Example:**

``` json
{ "type": "input_audio_buffer.commit" }
```

------------------------------------------------------------------------

### 8. `input_audio_buffer.clear`

**Purpose:**\
Clear the current buffered audio data. Useful if the user cancels
mid-speech.

**Example:**

``` json
{ "type": "input_audio_buffer.clear" }
```

------------------------------------------------------------------------

### 9. `response.create`

**Purpose:**\
Ask the model to generate a new response (text, audio, or both) based on
the conversation state.

**Example:**

``` json
{
  "type": "response.create",
  "response": {
    "modalities": ["text", "audio"],
    "instructions": "Summarize the user's last message."
  }
}
```

------------------------------------------------------------------------

### 10. `response.cancel`

**Purpose:**\
Cancel a currently streaming response generation.

**Example:**

``` json
{
  "type": "response.cancel",
  "response_id": "resp_12345"
}
```

------------------------------------------------------------------------

## 📤 Output Message Types (Server → Client)

These are messages that the API sends back to your application to
confirm operations, stream audio/text, or notify events.

------------------------------------------------------------------------

### 1. `conversation.item.created`

**Purpose:**\
Confirms that a new conversation item was successfully created.

**Example:**

``` json
{
  "type": "conversation.item.created",
  "item": {
    "id": "conv_item_99",
    "role": "user",
    "content": [{ "type": "input_text", "text": "Hello!" }]
  }
}
```

------------------------------------------------------------------------

### 2. `input_audio_buffer.committed`

**Purpose:**\
Acknowledges that the current audio buffer has been successfully
committed.

**Example:**

``` json
{ "type": "input_audio_buffer.committed" }
```

------------------------------------------------------------------------

### 3. `response.created`

**Purpose:**\
Indicates that the model has started generating a response.

**Example:**

``` json
{
  "type": "response.created",
  "response_id": "resp_12345"
}
```

------------------------------------------------------------------------

### 4. `response.output_text.delta`

**Purpose:**\
Provides a partial (streaming) chunk of generated text output.

**Example:**

``` json
{
  "type": "response.output_text.delta",
  "delta": "Hello there!"
}
```

------------------------------------------------------------------------

### 5. `response.audio.delta`

**Purpose:**\
Provides a partial (streaming) chunk of generated audio output.

**Example:**

``` json
{
  "type": "response.audio.delta",
  "audio": "<base64-encoded-wav>"
}
```

------------------------------------------------------------------------

### 6. `response.audio_transcript.delta`

**Purpose:**\
Provides a partial transcript of generated speech output.

**Example:**

``` json
{
  "type": "response.audio_transcript.delta",
  "delta": "The current temperature in Tokyo is..."
}
```

------------------------------------------------------------------------

### 7. `response.audio_transcript.done`

**Purpose:**\
Indicates the assistant's generated speech transcription is complete.

**Example:**

``` json
{ "type": "response.audio_transcript.done" }
```

------------------------------------------------------------------------

### 8. `response.done`

**Purpose:**\
Signals that the assistant has completed the current response
generation.

**Example:**

``` json
{
  "type": "response.done",
  "response_id": "resp_12345"
}
```

------------------------------------------------------------------------

### 9. `conversation.item.input_audio_transcription.completed`

**Purpose:**\
The full transcription of user input audio

**Example:**

``` json
{
 "unknow": "unknow"
}
```

------------------------------------------------------------------------

## Extra custome message type

Our custom messages

------------------------------------------------------------------------

### 1. `input_audio_session.start`

**Purpose:**\
Send required information to the backend and tell him to set up the conversation

**Example:**

``` json
{ 
  "type": "input_audio_session.start", 
  "user_id": "user_id", 
  "conversation_id": "conversation_id", 
  "course_id": "course_id" 
}
```

------------------------------------------------------------------------

## 💡 Typical Interaction Flow

    Client connects via WebSocket
    │
    ├─▶ session.update                # Configure session
    ├─▶ input_audio_buffer.append     # Send audio chunk
    ├─▶ input_audio_buffer.commit     # Done speaking
    ├─▶ response.create               # Request model reply
    │
    └─◀ response.output_text.delta    # Streaming text response
    └─◀ response.audio.delta          # Streaming audio response
    └─◀ response.done                 # Generation complete

------------------------------------------------------------------------

## 🧠 Notes

-   Input messages must be valid JSON with a `"type"` field.
-   The API uses duplex WebSocket communication, allowing simultaneous
    audio input/output.
-   Some message types may evolve or expand in future API versions.

------------------------------------------------------------------------

**Source:**\
- [OpenAI Realtime Conversations
Guide](https://platform.openai.com/docs/guides/realtime-conversations)\
- [OpenAI Community Discussions](https://community.openai.com)\
- [Azure OpenAI Realtime API
Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/realtime-audio-reference)
