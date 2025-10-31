# Copilot Instructions for Wotoha Music Bot

## Project Overview
Wotoha is a Discord music bot focused on simplicity and intuitive user experience. It supports playback from multiple platforms (YouTube, SoundCloud, NicoNico, Twitch) and is operated via Discord slash commands and interactive buttons.

## Architecture & Key Components
- **Entry Point:** `bot.py` initializes the Discord bot and loads cogs.
- **Cogs:** All bot features are modularized as cogs. The main music functionality is in `cogs/music.py`.
- **Utils:** Shared logic and state management are in `utils/` (`helpers.py`, `state.py`).
- **Config:** Bot configuration is handled in `config.py`.

## Developer Workflows
- **Run the Bot:**
  ```powershell
  python bot.py
  ```
- **Dependencies:**
  - All required packages are listed in `requirements.txt`. Install with:
    ```powershell
    pip install -r requirements.txt
    ```
- **Debugging:**
  - Use print/log statements in cogs for runtime inspection. No integrated test suite is present.

## Patterns & Conventions
- **Commands:**
  - All Discord commands are implemented as slash commands in cogs.
  - Button interactions are handled via Discord UI components in `music.py`.
- **Queue Management:**
  - Music queue and playback state are managed in `utils/state.py`.
- **Auto Disconnect:**
  - The bot automatically leaves voice channels when empty (see `music.py`).
- **Naming:**
  - Use descriptive function and variable names reflecting their Discord context (e.g., `play`, `skip`, `loop`).

## Integration Points
- **Discord.py:**
  - The bot uses the `discord.py` library for all Discord interactions.
- **External APIs:**
  - Music streaming is handled via platform URLs; extraction logic may be in `helpers.py`.

## Examples
- To add a new command, create a method in a cog class and decorate with `@commands.slash_command`.
- To share state, import and use functions/classes from `utils/state.py`.

## Key Files
- `bot.py`: Bot startup and cog loading
- `cogs/music.py`: Main music features and command handlers
- `utils/`: Shared helpers and state
- `config.py`: Configuration

---
_If any section is unclear or missing, please provide feedback for further refinement._
