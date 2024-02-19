
> [!Caution]
> **AVA IS A WORK IN PROGRESS. It is not available for release. There may be bugs and other issues. Explore at your own risk.** 

# Ava Assistant AI [Work in Progress]

Multiplatform voice assistant that handles daily user tasks using OpenAI custom assistants.

## Description

Ava Assistant AI is a voice assistant that uses speech recognition and it's own voice to interact and communicate with users. Ava is very basic at the moment but will be improved over time.

>[!Note]
> Uses [pyaimanager](https://github.com/joe-gutman/pyaimanager), made by me, as the library to communicate with the OpenAI assistants. 

## Demo 
- *wait time between request and response are sped up 2x and do not reflect the actual wait time)*

https://github.com/joe-gutman/ava-ai-assistant/assets/2061754/69501d9e-1ad5-44a9-acf3-88c8f04d3bbc

## Current Platforms
- Windows 11

## Current Features
- Get voice input from the user
- Sends and receives messages to and from the assistant server
- 
- Speaks to the user using a generated voice
- Run tools locally on specified devices (referencing device server address saved in DB)

## Current Tools
### Server Side
- Get current weather
- Get weather during closest 3 hour interval of a 5 day fourcast

### Client Side (Windows 11)
- Open 1 or more websites at a time
- Type out text based on request

### *Future Tools*
- Read highlighted text on specified device
- Search the internet and return results
- Open software on device

> [!Note]
>  Tools that take a device parameter will default to running the tool on the request's origin device
