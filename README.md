# telegram-all-forward

A simple script to forward all the messages of one chat (indivisual/group/channel) to another. Made using Telethon. Can be used to back up the contents of a chat to another place.

<p align="center">
  <img src="https://raw.githubusercontent.com/its-anya/telegram-all-forward/refs/heads/main/img/image.png" alt="showing forwarding terminal log" />
</p>



## Signing In

To use this Telegram forwarder, you need your Telegram account’s **API credentials**:

- `API_ID` – your numeric Telegram API ID  
- `API_HASH` – your unique Telegram API hash  

You can get them by following [Telegram API Documentation](https://my.telegram.org/apps).  

### Example `.env` configuration

```ini
# .env
API_ID=1234567
API_HASH=0123456789abcdef0123456789abcdef
STRING_SESSION=""  # optional: can leave empty if you want to login manually


## Installation

- Clone this repo and move into it to get started.

```shell
git clone https://github.com/its-anya/telegram-all-forward.git && cd telegram-all-forward
```

- Create a virtual environment and install dependencies.

```shell
python -m venv venv
```

For Windows, you may need to bypass execution policy to activate the virtual environment:

```shell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Install dependencies (if you encounter compilation errors on Windows, use the `--only-binary` flag):

```shell
pip install -r requirements.txt --only-binary=cffi
```

> Note: For Windows, the process for activating a virtual environment is different, search Google.

## Setup

You must have the `api_id` and `api_hash` as environment variables.
You may simply create a file named `.env` in the project directory and paste the following into it.

```shell
api_id=12345
api_hash=kjfjfk9r9JOIJOIjoijf9wr0w
```

**Replace the above values with the actual values for your telegram account.**

After this you need to create and fill up the `config.ini` file with your forwarding configurations.

## Configuration

- The `from` and `to` in the `config.ini` has to be a **username/phone/link/chat_id** of the chat.
- The chat id is the best way for configurations. It will always be accurate. To get the chat id of a chat, forward any message of the chat to [@userinfobot](https://telegram.me/userinfobot)
- You may have as many as forwarding pairs as you wish. Make sure to give a unique header to each pair. Follow the syntax shown below.

```ini
[name of forward1]
; in the above line give any name as you wish
; the square brackets around the name should remain
from = https://t.me/someone
to = -1001235055711
offset = 0
; the offset will auto-update, keep it zero initially
[another name]
; the name of section must be unique
from = @username
to = @anothername
offset = 0
```

> **Note**:Any line starting with `;` in a `.ini` file, is treated as a comment.

## Offset

- When you run the script for the first time, keep `offset=0`.
- When the script runs, the value of offset in `config.ini` gets updated automatically.
- Offset is basically the id of the last message forwarded from `from` to `to`.
- When you run the script next time, the messages in `from` having an id greater than offset (newer messages) will be forwarded to  `to`. That is why it is important not to loose the value of `offset`.

## Handling FloodWaitError (Rate Limits)

Telegram enforces rate limits to prevent abuse. If you encounter a `FloodWaitError`, the script will automatically wait for the required time before continuing. However, for the final summary messages, you may need to manually wait.

If you see an error like:
```
FloodWaitError: A wait of 2891 seconds is required
```

This means you need to wait approximately 48 minutes before running the script again. You can use the `check_flood_wait.py` script to calculate when you can run the forwarder again:

```shell
python check_flood_wait.py
```

To reduce the likelihood of hitting rate limits:
1. Avoid running the script too frequently
2. Forward smaller batches of messages at a time
3. The script now includes small delays between messages to help prevent rate limiting

## Execution

After setting up the `config.ini`, run the `forwarder.py` script.

```shell
python forwarder.py
```

You have to login for the first time using your phone number (inter-national format) and login code.

A session file called `forwarder.session` will be generated. 
**Please don't delete this and make sure to keep this file secret.**
